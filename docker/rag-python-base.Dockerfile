
FROM ghcr.io/snosachyev/transformer-base:latest

WORKDIR /app

COPY ./docker/requirements.txt /tmp/requirements.txt

RUN python -m pip install --no-cache-dir \
    -r /tmp/requirements.txt

RUN python -c "import torch; print('Torch:', torch.__version__); print('CUDA:', torch.version.cuda)"
