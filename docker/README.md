
# Шаг 1. Локально создаем токен для доступа к GitHub Registry

    Вы не можете зайти в реестр GitHub со своего компьютера по обычному паролю. Нужен персональный токен (PAT):
    1. В вашем аккаунте GitHub перейдите в Settings (Настройки) -> Developer settings -> Personal access tokens -> Tokens (classic).
    2. Нажмите Generate new token (classic).
    3. Дайте ему любое имя и обязательно отметьте галочку write:packages (галочка read:packages проставится сама).
    4. Нажмите Generate и скопируйте получившийся длинный токен (больше вы его не увидите).

# Шаг 2. Заливаем образы со своего компьютера в хранилище GitHub

    (замените ВАШ_GITHUB_ЛОГИН на ваш реальный никнейм на GitHub в нижнем регистре):
    1. Авторизуемся в GitHub Registry (вставьте скопированный токен вместо слова ТОКЕН):bash
    echo "ТОКЕН" | docker login ghcr.io -u ВАШ_GITHUB_ЛОГИН --password-stdin
    Используйте код с осторожностью.
    2. Собираем и отправляем transformer-base:bash
    docker build -t ghcr.io/ВАШ_GITHUB_ЛОГИН/transformer-base:latest -f ./docker/transformer-base.Dockerfile .
    docker push ghcr.io/ВАШ_GITHUB_ЛОГИН/transformer-base:latest
    Используйте код с осторожностью.
    3. Собираем и отправляем rag-python-base:bash
    docker build -t ghcr.io/ВАШ_GITHUB_ЛОГИН/rag-python-base:latest -f ./docker/rag-python-base.Dockerfile .
    docker push ghcr.io/ВАШ_GITHUB_ЛОГИН/rag-python-base:latest


# Как связать пакет с репозиторием и дать права на чтение:

1. Зайдите на GitHub в свой профиль и перейдите на вкладку Packages (Пакеты).
2. Выберите пакет rag-python-base (а затем повторите то же самое для transformer-base).
3. В правом меню нажмите кнопку Package settings (Настройки пакета).
4. Прокрутите страницу вниз до раздела Manage Actions access (Управление доступом Actions).
5. Нажмите кнопку Add Repository (Добавить репозиторий).
6. Введите имя вашего репозитория (ai_multy_agent) и добавьте его.
7. После добавления убедитесь, что для этого репозитория в выпадающем списке выставлены права Read (Чтение).

## Второй вариант 
(если ваш репозиторий публичный или вам не жалко открыть этот базовый образ): в самом низу страницы настроек пакета в Danger Zone нажмите Change visibility и сделайте пакет Public.