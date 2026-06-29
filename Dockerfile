# Ambiente de análise para o trabalho de Lei dos Grandes Números.
# Imagem slim do Python + dependências científicas + JupyterLab.
FROM python:3.12-slim

# Evita .pyc e garante saída de log sem buffer (útil ao rodar o script).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependências de sistema:
#  - curl: diagnóstico de rede;
#  - texlive + latexmk: compilação do trabalho escrito (trabalho/trabalho.tex).
# Conjunto de pacotes texlive escolhido para cobrir o preâmbulo do .tex
# (babel-pt, amsmath, siunitx, booktabs, microtype, hyperref, lmodern, etc.).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        latexmk \
        lmodern \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-lang-portuguese \
        texlive-science \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

# Instala as dependências primeiro para aproveitar o cache de camadas do Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# O código do projeto entra via volume (ver docker-compose.yml), então não
# copiamos os notebooks/dados aqui — assim eles persistem no host.

EXPOSE 8888

# Sobe o JupyterLab acessível de fora do container, sem token (uso local/acadêmico).
CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--ServerApp.token=", \
     "--ServerApp.password=", \
     "--ServerApp.root_dir=/work"]
