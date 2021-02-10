FROM continuumio/miniconda3
EXPOSE 8501
WORKDIR /app
COPY environment.yml .
RUN conda env create -f environment.yml
SHELL ["conda", "run", "-n", "acoustic_env", "/bin/bash", "-c"]
COPY . .
RUN pip install -e .
ENTRYPOINT ["conda", "run", "-n", "acoustic_env", "streamlit", "run", "app.py"]