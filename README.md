# 🤖 Refri Auto Bot - Automação de Atendimento WhatsApp

## 📌 O que é este projeto?

Este é um sistema de atendimento automatizado (Chatbot) para WhatsApp, desenvolvido em **Python** utilizando o micro-framework **Flask** e integrado à **Evolution API** (sistema de mensageria via Webhook). 

O projeto foi construído sob medida para a **Refri Auto**, uma oficina especializada em ar condicionado automotivo. Ele atua como um "recepcionista virtual" que trabalha 24 horas por dia, sendo responsável por fazer a triagem inicial dos clientes, tirar dúvidas frequentes e auxiliar na coleta de informações estruturadas para agendamentos.

### 🎯 O problema que este bot resolve:
Antes da automação, a oficina recebia mensagens fora do horário de expediente ou perdia tempo respondendo repetidamente às mesmas perguntas sobre preços de serviços básicos. Este bot automatiza esse processo, melhorando a experiência do cliente (que recebe respostas instantâneas) e liberando a equipe humana para focar apenas nos atendimentos complexos e na execução dos serviços.

---

## ✨ Principais Funcionalidades

O sistema foi programado com diversas regras de negócio para tornar a interação o mais natural e eficiente possível:

* **🕒 Controle Inteligente de Horário Comercial:** Utilizando a biblioteca `pytz` para garantir o fuso horário correto (Brasília), o bot sabe exatamente quando a oficina está aberta (Seg-Sex: 08h às 18h | Sáb: 08h às 13h). Se um cliente envia mensagem de madrugada ou no domingo, o sistema o avisa automaticamente sobre a indisponibilidade e registra a tentativa de contato.

* **📋 Menu Interativo de Triagem:** Fornece um menu de autoatendimento numérico (Opções de 1 a 5) que direciona o cliente para:
  1. Agendamento externo (captura de dados).
  2. Informações sobre agendamento na oficina.
  3. Pré-orçamento para carga de gás.
  4. Pré-orçamento para higienização.
  5. Contato direto com o setor financeiro.

* **🧠 Máquina de Estados (Memória de Atendimento):** Diferente de bots simples que apenas respondem palavras-chave, este bot possui "memória de contexto". Ele utiliza um banco de dados local em JSON (`banco_bot.json`) para lembrar em qual etapa da conversa o cliente está. *Exemplo: Se o cliente escolhe a opção 1, o bot entra no estado `aguardando_dados` e espera o usuário digitar o modelo do carro e endereço antes de finalizar e limpar o fluxo.*

* **🔄 Controle de Saudação Diária (Anti-Spam):** Para garantir uma boa experiência de usuário (UX), o bot grava a data da última interação de cada número. Dessa forma, ele só envia o menu de boas-vindas **uma vez por dia**. Se o cliente continuar mandando mensagens ao longo do dia, o bot não será intrusivo repetindo o menu.

* **✍️ Simulação de Digitação Humana:** Para não parecer um robô frio, o sistema calcula dinamicamente um tempo de espera (delay) baseado na quantidade de caracteres da resposta que será enviada. Durante esse tempo, ele dispara um evento para a API do WhatsApp mostrando o status *"escrevendo..."* (`composing`) na tela do cliente.

* **🚫 Filtros de Segurança e Duplicidade:**
  * **Ignora Grupos:** Mensagens vindas de IDs com `@g.us` são descartadas.
  * **Ignora o Próprio Bot:** Evita loops infinitos ignorando mensagens com a flag `fromMe`.
  * **Controle de Webhooks:** Mantém um registro em memória (`Set`) dos IDs das mensagens já processadas, evitando que o bot responda duas vezes caso a API dispare o mesmo webhook acidentalmente.

---

## 🛠️ Tecnologias e Arquitetura

* **Linguagem:** Python 3
* **Servidor Web:** Flask (recebimento ágil de requisições POST/GET)
* **Integração:** Evolution API (comunicação com o WhatsApp via Webhook)
* **Manipulação de Tempo:** `datetime` e `pytz`
* **Armazenamento:** Estrutura de dados em JSON para persistência leve de estado e histórico de interações.
