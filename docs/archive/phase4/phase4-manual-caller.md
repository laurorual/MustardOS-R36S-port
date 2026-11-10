# C105 — caller manual instalado

O próximo componente reúne o caller já validado como arquivos próprios em
`/usr/libexec/muos-caller`, sem copiar uma rootfs inteira para cada incremento.
O pacote tem **17 arquivos, um diretório e 60.276 bytes**. Dez scripts originais
MIT permanecem byte a byte iguais ao contexto C104: adapter, app-launch, cycle,
frontend-libs, installed-host, installed-store, select, store-base, store e worker.
Os demais arquivos são funções/entrada, inventários públicos, contrato e licença.

O preparador passou a aceitar o cabeçalho SPDX da biblioteca `adapter.sh`,
que é carregada com `.` e não tem shebang. A conferência do SHA original
continua obrigatória; nenhum script histórico foi alterado para contornar isso.

## Contrato e limites

Executar explicitamente com `sh /usr/libexec/muos-caller/caller.sh`:

- `check`: verifica o pacote e 142 dependências públicas, mídia, kernel/painel,
  raiz RO, diagnóstico C07 pronto, ausência de UI/token e PCM fechado.
- `stage <capsule>`: copia dez scripts para uma cápsula tmpfs própria, root0700,
  vinculada ao boot e ao pacote. Não sobrescreve nem repete tentativa parcial.
- `run <capsule> observe`: exige os scripts, dez assets públicos fixados,
  metadados do snapshot existente, ROM GB privada e função `load`. Recusa
  fallback de ELF/core/host e uma segunda execução. O worker original usa o
  isolamento por namespace e os limites de 240/210/45 segundos.

A preparação completa dos assets/cápsula ainda pertence ao harness explícito.
Este componente não é navegador geral de ROMs nem uma sessão independente
inteiramente preparada pelo comando `run`. A sessão gráfica pelo entrypoint
instalado precisa de um incremento próprio. Não acrescenta autostart, serviço,
emulador, ROM, estado, chave, seed ou identidade privada ao payload instalado.

O inventário do pacote exclui o hash da chave autorizada, presente somente na
guarda privada da implantação. A instalação usa o mesmo modelo C79/C102,
incluindo template, asound.conf, identidade4 e metadados dos 141 arquivos já
qualificados. Não cria visões inteiras de /etc ou /mnt pelo contorno C99.

## Boot e transação

A retomada encontrou boot80 com falha USB e recuperação física de SSH. Essa
falha permaneceu registrada. Um pedido único de reboot normal80→81 teve
intent/claim fsync antes do despacho; somente essa ação admite o diagnóstico
USB falhado com evidências exatas de recuperação e todas as demais guardas.
Não remove nem reativa claims/tokens antigos.

A observação81 passou por `c25_ready` completo e vinculou contador/UUID reais
à prova C104. Gera a guarda de81 a partir do mesmo modelo de arquivos e do
layout instalado; não substitui UUID por texto em um runner antigo nem altera
o contrato exato78→79 do C104. O observador não lê seeds e não repete C97.
O usuário confirmou que o console estava conectado após o reboot.

A transação deriva do adaptador MIT C76, com escopo próprio de 17 folhas e um
diretório. Preserva ausência anterior, fingerprint privado, mountinfo global
e infraestrutura. Há uma única chamada de aplicação; em caso de interrupção,
coletar a mesma tentativa. Rollback remove somente folhas correspondentes
ao plano e diretório próprio vazio; vizinhos desconhecidos são preservados.

## Validação

Pacote `manual-caller/package.er1m0bnf`; checks `checks.hpybluli`:
**43 casos** de integridade, modos, aliases, colisão, stage parcial/repetido,
boot antigo, assets/role/ROM e execução única, mais transação real do novo
escopo em árvores descartáveis, com falhas em guard/rw/mkdir/verify/sync/ro e
nas folhas1/9/17. Sem executar ELF, core, ROM ou namespaces nesses fixtures.

Quatro grupos adicionais testam o vínculo de boot, com 12 variantes negativas.
A guarda recém-gerada conserva exatamente o inventário de hashes da guarda
anterior e a chamada `c25_ready`; passou em `sh -n`. Cada operação nativa
exige o pacote e as fontes correspondentes aos checks. O sucesso offline
não qualifica a sessão gráfica pelo caller instalado.

**Resultado nativo aprovado no boot81:** `install.322dqnrs`, observação
`observe.70yc6fne`, reboot `reboot-recovered.zrm_92lu`. Os 17 arquivos foram
instalados sem substituir arquivos existentes. `check` conferiu o pacote e
142 dependências públicas; `stage` copiou os dez scripts para RAM com modos e
bytes corretos. Repetir `stage` e tentar `run` sem os assets foram recusados.
Nenhuma interface gráfica, ROM, core ou serviço de UI foi executado nesta
instalação; a sessão gráfica pelo entrypoint continua pendente.

Aplicação0, fingerprint privado e mountinfo global iguais, infraestrutura
PID/starttime preservada. As cápsulas de aplicação e staging foram removidas;
raiz RO, layout C102 e guardas preservados na última conferência. Todos os
recibos nativos esperados terminaram0. Não repetir o apply nem remover
`dispatch.claim` ou `recovered-reboot.claim`: são tentativas consumidas.
Prova sanitizada em `dist/phase4/manual-caller-installed`, com payload público,
fontes e recibos agregados, sem guardas privados, ROM, ELF, seed ou UUID real.

## Próximo incremento

Qualificar menu → GB → menu usando o entrypoint instalado, com assets em RAM,
somente restauração do snapshot e o worker original. Confirmar imagem/input/
áudio/Fn+L2/Fn+Start e a restauração do ambiente. Navegador geral, execução
automática e demais lacunas de energia/SRAM/longa duração continuam separados.
