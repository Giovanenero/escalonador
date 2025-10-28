ifeq ($(OS),Windows_NT)
    PYTHON = python
    RM = del /Q
    RMDIR = rmdir /S /Q
    ACTIVATE = venv\Scripts\activate
    PIP = venv\Scripts\pip
    EXECUTABLE = dist\main.exe
else
    PYTHON = python3
    RM = rm -f
    RMDIR = rm -rf
    ACTIVATE = source venv/bin/activate
    PIP = venv/bin/pip
    EXECUTABLE = dist/main
endif

# ======================================================
# Alvo padrão: cria venv, instala deps, executa o programa
# ======================================================
all: run

# Cria o venv se não existir
venv:
	@if [ ! -d "venv" ]; then \
		echo ">>> Criando ambiente virtual..."; \
		$(PYTHON) -m venv venv; \
	fi

deps: venv
	@echo ">>> Instalando dependências..."; \
	$(PIP) install --upgrade pip >nul 2>&1 || true; \
	$(PIP) install -r requirements.txt

run: deps
	@echo ">>> Executando o programa..."; \
	$(PYTHON) main.py

build: deps
	@echo ">>> Instalando PyInstaller (se necessário)..."; \
	$(PIP) install pyinstaller >nul 2>&1 || true
	@echo ">>> Gerando executável..."; \
	$(PYTHON) -m PyInstaller --onefile --noconsole --icon=icone.ico \
	    --hidden-import=PIL.Image \
	    --hidden-import=PIL.ImageTk \
	    --hidden-import=PIL._tkinter_finder \
	    main.py
	@echo ">>> Executável criado em: $(EXECUTABLE)"

clean:
	-$(RM) plt.png 2>nul || true
	-$(RMDIR) __pycache__ 2>nul || true
	-$(RMDIR) build 2>nul || true
	-$(RMDIR) dist 2>nul || true
	-$(RM) main.spec 2>nul || true
	-$(RMDIR) venv 2>nul || true
	@echo "Limpeza completa!"

.PHONY: all venv deps run build clean
