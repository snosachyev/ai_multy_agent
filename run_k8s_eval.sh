#!/usr/bin/env bash
set -euo pipefail

ENV=${1:-"local"}
EVAL_SCRIPT=${2:-"evaluation/researcher/run_evaluation.py"}

echo "📦 Упаковка папки evaluation/ в архив..."
tar --exclude='__pycache__' -czf /tmp/eval.tar.gz -C . evaluation

kubectl create configmap eval-code-cm \
  --from-file=eval.tar.gz=/tmp/eval.tar.gz \
  --dry-run=client -o yaml | kubectl apply -f -

rm -f /tmp/eval.tar.gz

if [ "$ENV" == "local" ]; then
  OLLAMA_TARGET=$(kubectl get svc ollama-service -o jsonpath='{.spec.clusterIP}')
  PG_TARGET=$(kubectl get svc postgres-metrics -o jsonpath='{.spec.clusterIP}')
  ORCH_TARGET=$(kubectl get svc rag-orchestrator -o jsonpath='{.spec.clusterIP}')
  RES_TARGET=$(kubectl get svc rag-researcher -o jsonpath='{.spec.clusterIP}')
else
  OLLAMA_TARGET="ollama-service"
  PG_TARGET="postgres-metrics"
  ORCH_TARGET="rag-orchestrator"
  RES_TARGET="rag-researcher"
fi

echo "🚀 Запуск оценки ($EVAL_SCRIPT) в среде: $ENV..."
kubectl delete job rag-eval-job --ignore-not-found

sed -e "s/OLLAMA_HOST_PLACEHOLDER/${OLLAMA_TARGET}/g" \
    -e "s/PG_HOST_PLACEHOLDER/${PG_TARGET}/g" \
    -e "s/ORCH_HOST_PLACEHOLDER/${ORCH_TARGET}/g" \
    -e "s/RES_HOST_PLACEHOLDER/${RES_TARGET}/g" \
    -e "s|EVAL_SCRIPT_PLACEHOLDER|${EVAL_SCRIPT}|g" \
    k8s/eval-job.yaml | kubectl apply -f -

echo "⏳ Ожидание старта пода..."
kubectl wait --for=condition=Ready pod -l job-name=rag-eval-job --timeout=60s || true

echo "📜 Логи выполнения оценки:"
kubectl logs -f job/rag-eval-job
