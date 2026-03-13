# 🛠️ Structure Builder Pro: Engenharia de Workspaces 📁✨

![Status](https://img.shields.io/badge/Status-Versão_5.3-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![UI](https://img.shields.io/badge/UI-Eel%20%7C%20HTML5%20%7C%20CSS3-orange)

O **Structure Builder Pro** evoluiu de um simples criador de diretórios para uma estação de trabalho completa para gerenciamento de hierarquias de arquivos. Combinando a robustez do Python com a fluidez de interfaces web modernas, ele oferece controle total sobre a organização de dados em larga escala.

---

## 🚀 Funcionalidades de Engenharia Sênior

### 🔄 Módulo de Espelhamento Inteligente
O recurso mais poderoso para quem precisa reorganizar projetos complexos em tempo real:
*   **Arraste de Conteúdo Puro**: Ao arrastar uma pasta, o sistema extrai todos os arquivos recursivamente para o destino, mantendo a estrutura original intacta como um contêiner persistente.
*   **Auto-Scroll Dinâmico**: Navegação fluida em árvores gigantes; o scroll acompanha o movimento do mouse durante o arraste.
*   **Sincronia Bidirecional**: Dois painéis sincronizados (Edição vs Visualização) garantem que você veja o impacto de cada mudança antes de aplicá-la fisicamente no Windows Explorer.

### 🧠 Central de Gestão de Memórias (Snapshots)
Esqueça o medo de perder edições manuais complexas:
*   **Multi-Snapshot Registry**: Salve "Lembranças" de múltiplos projetos simultaneamente. Cada memória é chaveada pelo caminho físico da pasta.
*   **Identificação Fiel**: Snapshots assumem o nome real da pasta raiz e preservam data e hora exatas para rastreabilidade histórica.
*   **Gestão de Recursos**: Interface de alto contraste para recuperar ou excluir lembranças, com liberação imediata de espaço em disco e memória RAM.

### 📊 Visualização e Diagnóstico
*   **Contagem Unificada**: Ícones de pastas exibem o total recursivo de arquivos internamente, eliminando ambiguidades.
*   **Diagramas Automáticos**: Gere diagramas Mermaid em tempo real da sua estrutura e exporte como SVG para documentação.
*   **Harmonia Cromática**: Interface otimizada para os modos Dark e Light, preservando o contraste e a legibilidade profissional.

---

## 🎨 Arquitetura de Interface (UX)

O software utiliza o padrão **Glassmorphism** e **Modern UI**:
1.  **Sidebar de Acesso Rápido**: Gerenciamento de modelos, biblioteca e temas.
2.  **Painel de Espelhamento**: Área de trabalho expandida com redimensionamento horizontal e vertical dinâmico.
3.  **Motor de Persistência**: Todo o estado da sua sessão é guardado silenciosamente no AppData, permitindo retomar o trabalho exatamente de onde parou.

---

## ⌨️ Comandos e Atalhos Profissionais

*   <kbd>F2</kbd>: Renomeação inteligente (com preservação de extensão para arquivos).
*   <kbd>Delete</kbd>: Exclusão cirúrgica de itens na árvore ou lembranças no registro.
*   <kbd>Ctrl</kbd> + <kbd>N</kbd>: Criação instantânea de novos contêineres.
*   **Botão Voltar**: Navegação de saída destacada para maior orientação espacial.

---

## 🛠️ Stack Tecnológica

*   **Back-end**: Python 3.12+ utilizando `Eel` para ponte de comunicação assíncrona.
*   **Front-end**: HTML5, CSS3 (Variáveis Dinâmicas) e JavaScript Vanila (DOM Virtual).
*   **Motor de Arquivos**: Lógica recursiva sênior com suporte a caminhos longos (UNC) no Windows.
*   **Persistência**: JSON estruturado com compactação automática de dados.

---

## 📖 Como Iniciar

1.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
2.  Execute o maestro:
    ```bash
    python bridge.py
    ```

---

## 📝 Documentação e Integridade

Acesse o **Manual Interativo** diretamente pela interface para detalhes técnicos sobre o motor de sincronização e regras de segurança de dados. O sistema prioriza a não-regressão e a integridade do sistema de arquivos do usuário.

---

> **"A estrutura é a espinha dorsal da eficiência."** 📁✨  
> *Builder Pro: Projetado por engenheiros, para engenheiros.*
