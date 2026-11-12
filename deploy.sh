#!/usr/bin/env bash
set -euo pipefail

ENV=${1:-"local"}
MODEL_LOCAL="qwen2.5:3b"
MODEL_PROD="qwen2.5:7b"

echo "🚀 Запуск развертывания RAG Platform в режиме: $ENV"

# 1. Применяем базовую инфраструктуру и хранилища
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/ollama.yaml

# Вспомогательная функция для загрузки образа только при его отсутствии в Minikube
load_if_missing() {
  local img=$1
  # Ищем точное совпадение имени образа в списке кэша minikube
  if minikube image ls | grep -q "$img"; then
    echo "✔️ Образ $img уже в кэше Minikube, пропускаем."
  else
    echo "📥 Загрузка $img в Minikube..."
    minikube image load "$img"
  fi
}

if [ "$ENV" == "local" ]; then
  echo "📦 [LOCAL] Проверка и загрузка локальных образов в Minikube..."
  
  # Приводим локальные имена к стандарту GHCR
  docker tag rag-orchestrator:latest ghcr.io/snosachyev/rag-platform-orchestrator:latest 2>/dev/null || true
  docker tag rag-director:latest ghcr.io/snosachyev/rag-director:latest 2>/dev/null || true
  docker tag rag-analyst:latest ghcr.io/snosachyev/rag-analyst:latest 2>/dev/null || true
  docker tag rag-finalizer:latest ghcr.io/snosachyev/rag-finalizer:latest 2>/dev/null || true
  docker tag rag-researcher:latest ghcr.io/snosachyev/rag-researcher:latest 2>/dev/null || true

  # Загружаем только те образы, которых еще нет в кластере
  load_if_missing "ghcr.io/snosachyev/rag-platform-orchestrator:latest"
  load_if_missing "ghcr.io/snosachyev/rag-director:latest"
  load_if_missing "ghcr.io/snosachyev/rag-analyst:latest"
  load_if_missing "ghcr.io/snosachyev/rag-finalizer:latest"
  load_if_missing "ghcr.io/snosachyev/rag-researcher:latest"
  load_if_missing "ollama/ollama:latest"
  load_if_missing "busybox:1.36"

  load_if_missing "postgres:16-alpine"
  load_if_missing "prom/prometheus:latest"
  load_if_missing "grafana/grafana:latest"


  echo "📁 [LOCAL] Проверка и загрузка данных в PersistentVolumeClaim..."
  
  # Удаляем старый под-помощник, если он остался от прерванного запуска
  kubectl delete pod data-loader --grace-period=0 --force 2>/dev/null || true

  kubectl run data-loader --image=busybox:1.36 --restart=Never \
    --overrides='{"spec":{"containers":[{"name":"loader","image":"busybox:1.36","command":["sleep","3600"],"volumeMounts":[{"name":"vol","mountPath":"/mnt"}]}],"volumes":[{"name":"vol","persistentVolumeClaim":{"claimName":"rag-data-pvc"}}]}}'
  
  kubectl wait --for=condition=Ready pod/data-loader --timeout=60s
  kubectl exec data-loader -- mkdir -p /mnt/data /mnt/huggingface
  
  # 1. Проверяем наличие chunked.pkl внутри PVC
  if kubectl exec data-loader -- test -f /mnt/data/chunked.pkl; then
    echo "✔️ Файл chunked.pkl уже есть в PVC, пропускаем."
  else
    echo "📥 Копирование chunked.pkl в PVC..."
    kubectl cp ./data/chunked.pkl data-loader:/mnt/data/chunked.pkl
  fi
  
  # 2. Проверяем наличие кэша моделей внутри PVC
  if kubectl exec data-loader -- test -d /mnt/huggingface/hub; then
    echo "✔️ Кэш Hugging Face уже загружен в PVC, пропускаем."
  elif [ -d "$HOME/.cache/huggingface" ]; then
    echo "📥 Упаковка и копирование кэша Hugging Face в PVC..."
    tar -czf /tmp/hf.tar.gz -C "$HOME/.cache/huggingface" .
    kubectl cp /tmp/hf.tar.gz data-loader:/tmp/hf.tar.gz
    kubectl exec data-loader -- tar -xzf /tmp/hf.tar.gz -C /mnt/huggingface
    rm -f /tmp/hf.tar.gz
  fi
  
  kubectl delete pod data-loader --grace-period=0 --force

fi

# 2. Применяем сервисы и деплойменты приложений
kubectl apply -f k8s/apps.yaml

# 3. Ожидаем запуска Ollama и скачиваем нужную модель
echo "⏳ Ожидание запуска Ollama..."
kubectl rollout status deployment/ollama-service --timeout=300s
OLLAMA_POD=$(kubectl get pods -l app=ollama -o jsonpath='{.items[0].metadata.name}')

TARGET_MODEL=$([ "$ENV" == "local" ] && echo "$MODEL_LOCAL" || echo "$MODEL_PROD")
echo "🧠 Проверка/загрузка модели $TARGET_MODEL..."
kubectl exec "$OLLAMA_POD" -- ollama pull "$TARGET_MODEL"

# 4. Настройка сетевых адресов под среду
if [ "$ENV" == "local" ]; then
  echo "🔧 [LOCAL] Патчим ConfigMap актуальными ClusterIP для обхода бага DNS в Minikube..."
  OLLAMA_IP=$(kubectl get svc ollama-service -o jsonpath='{.spec.clusterIP}')
  DIRECTOR_IP=$(kubectl get svc rag-director -o jsonpath='{.spec.clusterIP}')
  RESEARCHER_IP=$(kubectl get svc rag-researcher -o jsonpath='{.spec.clusterIP}')
  ANALYST_IP=$(kubectl get svc rag-analyst -o jsonpath='{.spec.clusterIP}')
  FINALIZER_IP=$(kubectl get svc rag-finalizer -o jsonpath='{.spec.clusterIP}')

  kubectl patch configmap rag-config -p "{\"data\":{
    \"LLM_MODEL\":\"${TARGET_MODEL}\",
    \"OLLAMA_BASE_URL\":\"http://${OLLAMA_IP}:11434\",
    \"DIRECTOR_SERVICE_URL\":\"http://${DIRECTOR_IP}:8001\",
    \"RESEARCHER_SERVICE_URL\":\"http://${RESEARCHER_IP}:8002\",
    \"ANALYST_SERVICE_URL\":\"http://${ANALYST_IP}:8003\",
    \"FINALIZER_SERVICE_URL\":\"http://${FINALIZER_IP}:8004\"
  }}"

  echo "🔄 Перезапускаем сервисы с обновленными локальными IP..."
  kubectl rollout restart deployment rag-orchestrator rag-researcher rag-director rag-analyst rag-finalizer
fi

echo "✅ Развертывание завершено! Проверка статуса подов:"
kubectl get pods

if [ "$ENV" == "local" ]; then
  echo "🌐 Swagger UI доступен по адресу: $(minikube service rag-orchestrator --url)/docs"
  echo "📊 Grafana доступна по адресу: $(minikube service grafana --url) (логин: admin, пароль: admin_secure_password)"
  echo "📈 Prometheus доступен по адресу: $(minikube service prometheus --url)"

fi
