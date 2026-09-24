FROM amancevice/pandas:2.2.2

RUN pip install --no-cache-dir matplotlib seaborn scikit-learn scipy tabulate

ENV MPLBACKEND=Agg
# Hide pandas FutureWarnings: they flood the agents' context without helping them.
ENV PYTHONWARNINGS=ignore::FutureWarning
WORKDIR /workspace
