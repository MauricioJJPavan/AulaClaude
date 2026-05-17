# Ações 2025

App web em Python usando Streamlit para buscar, analisar e exibir cotações de PETR4, ITUB4 e VALE3 em 2025.

## Objetivo

- Buscar dados de ações com `yfinance`
- Manipular séries históricas com `pandas`
- Exibir gráficos interativos com `plotly`
- Criar um app de visualização em `streamlit`

## Estrutura

- `app.py`: aplicação Streamlit
- `requirements.txt`: dependências do projeto
- `README.md`: documentação do projeto

## Como executar

1. Crie o ambiente virtual:
   ```powershell
   python -m venv .venv
   ```

2. Ative o ambiente:
   ```powershell
   .venv\Scripts\activate
   ```

3. Instale as dependências:
   ```powershell
   pip install -r requirements.txt
   ```

4. Execute o app:
   ```powershell
   streamlit run app.py
   ```

## Observações

- Use `.venv` antes de instalar dependências.
- Use `requirements.txt` para registrar as dependências.
- O app traz preços ajustados e retorno acumulado para 2025.
