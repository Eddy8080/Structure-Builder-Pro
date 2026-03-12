1. Sistema de Licenciamento (Proteção e Monetização)


  Para um software distribuído (Desktop), o licenciamento deve equilibrar segurança com experiência do usuário.


  A Estratégia Recomendada:
   * Identificação de Hardware (HWID): Gerar uma "impressão digital" da máquina (Baseada na CPU, Placa-mãe ou MAC Address). Isso evita que uma única
     licença seja copiada para múltiplos PCs.
   * Para multiplos Pcs explorar a possibilidade de gerar para cada PC
   * Validação Híbrida:
       * Online: O app consulta uma API (ex: Supabase, Firebase ou um servidor simples em Python/FastAPI) para validar a chave na primeira execução.
       * Offline (Cache): Armazenar um token criptografado localmente para permitir o uso sem internet por um período (ex: 7 dias), revalidando
         silenciosamente quando houver conexão.
       * Criar botão para o usuário caso eu como Engenehiro de software disponibilize  uma correção.
       
   * Tipos de Licença: Implementar suporte a licenças por Assinatura mensal ou anual e Trial de 15 dias para teste, sendo que por assinatura com a possibilidade de travar o uso sem permissão do usuário, quando o usuário for desbloquear aparecerá uma mensagem informando a renovação mensal, mas antes do bloqueio infromar por e-mail automático.

   Ter uma única licença Master que pode ser usada abertamente mas que possa ser alterada quando for percebido que não existe autorização de uso.


  Fluxo Técnico:
   1. Usuário insere a chave.
   2. App envia Key + HWID para o servidor.
   3. Servidor valida e retorna um Token JWT assinado.
   4. App armazena o token e libera as funcionalidades do Eel (Frontend).

  ---

  2. Atualizações Automáticas via GitHub (CI/CD Desktop)

  A integração com o GitHub permite que o seu fluxo de desenvolvimento (Git Push) alimente diretamente a base de usuários.


  A Estratégia Recomendada:
   * GitHub Releases: Em vez de monitorar apenas o código, o app deve monitorar a seção de Releases do repositório. Quando você cria uma nova tag
     (ex: v2.1.0), o GitHub gera os binários.
   * Verificação de Versão: O Python consulta a API pública do GitHub (/repos/{user}/{repo}/releases/latest) no início do programa.
   * O Desafio do "Auto-Replace": Um executável em execução não pode se sobrescrever no Windows.


  Arquitetura do Updater:
   1. Detecção: O app atual compara a versão local (ex: no README.md ou variável interna) com a do GitHub.
   2. Notificação: Um aviso aparece na interface Web: "Nova versão disponível!".
   3. Download: O app baixa o novo instalador (.exe gerado pelo seu Inno Setup) para uma pasta temporária.
   4. Troca de Processo:
       * O App principal inicia um pequeno script "Updater.exe" (ou o próprio instalador) e se fecha imediatamente.
       * O instalador roda em modo silencioso (/SILENT), substitui os arquivos e reinicia o software.

  ---

  Análise de Viabilidade e Próximos Passos



  ┌─────────┬──────────────┬─────────────────────────────────────────────────────────────┐
  │ Recurso │ Complexidade │ Ferramentas Sugeridas                                       │
  ├─────────┼──────────────┼─────────────────────────────────────────────────────────────┤
  │ Licença │ Média        │ cryptography (Python), wmi (para HWID), API REST externa.   │
  │ Updates │ Alta         │ requests (Python), GitHub API, Inno Setup (Silent Install). │
  └─────────┴──────────────┴─────────────────────────────────────────────────────────────┘



  Considerações Finais do Engenheiro:
  A arquitetura atual do seu projeto (Python + Eel) é ideal para isso. O Python gerencia a lógica pesada de rede e criptografia, enquanto o Eel
  fornece um feedback visual elegante sobre o progresso do download ou status da licença.


  Sugestão de Próximo Passo: Antes de automatizar tudo, o primeiro passo seria criar um pequeno módulo em bridge.py que apenas consulta a versão no
  GitHub e exibe um alerta no console. Uma vez que a comunicação funcione, expandimos para o download e o licenciamento.
  Não deve ser quebrado o código que está 100% funcional.

  Detalhamento das Etapas de Implementação:

  Parte 1: Módulo de Verificação de Versão (Infraestrutura Base)
   * Criar arquivo 'version_control.py' para isolar a lógica de rede.
   * Implementar consulta assíncrona à API do GitHub (Releases).
   * Criar arquivo local 'version.json' para controle interno da versão atual.
   * Comparar versão local vs remota e retornar status para o Frontend.

  Parte 2: Módulo de Licenciamento e HWID (Segurança)
   * Desenvolver coletor de Hardware ID (CPU + Motherboard) para vínculo único.
   * Estruturar integração com API externa (Supabase/Firebase) para validação de chaves (Keys).
   * Implementar criptografia AES para o token de cache local (uso offline).
   * Criar lógica de Trial (contador de dias) e verificação de expiração.

  Parte 3: Interface e Feedback (Eel/Frontend)
   * Adicionar indicador de "Versão Atual" e "Status de Licença" no rodapé da Sidebar.
   * Criar modal de "Nova Versão Disponível" com changelog simplificado.
   * Implementar tela de ativação de licença (input para a Key).
   * Adicionar botão de "Verificar Atualizações" manualmente no sistema.

  Parte 4: Automação do Instalador e Auto-Replace (Deployment)
   * Configurar parâmetros do Inno Setup para instalação silenciosa (/SILENT /SUPPRESSMSGBOXES).
   * Criar script auxiliar 'updater.exe' para gerenciar o fechamento do app principal e execução do instalador.
   * Criar a possibilidade de troubleshooting caso a atualização não tenha funcionando adequadamente. 
   * Testar fluxo completo de download -> substituição -> reinicialização.
   * Após atualização bem sucedida exibir uma caixa informando melhorias na aplicação mas não falando dos arquivos .py , e sim as melhorias que quando o usuário ler entenda, por exemplo: "ealizado atualização em modelos rápidos para não alterar o nome do modelo ou como adicionado nova função" como disse são exemplos para qualquer atualização. O manual será atualizado automaticamente e caixa que abrir terá a opção de ler manual ou fechar a caixa de diálogo.

  O que acha de começarmos a estruturar o módulo de Versão no futuro para testar essa comunicação com o GitHub? não altere o código ainda e entenda o projeto após ler.

  Este projeto vejo a necessidade de criar um painel para visualizar licenças ativas e isso será um novo projeto que pode ser feito em paralelo no caminho do projeto C:\Users\edilson.monteiro\Documents\projetos\Painel_Licenças

  Para o projeto e Estrutura de árvores deve ser implementado a atualização automática que servirá para outros projetos.

  NÃO ALTERE  NENHUM CÓDIGO 