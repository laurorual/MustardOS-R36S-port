# C22 — pacote de sessão independente do coordenador de boot

Em 29/10/2026 foi removida a dependência implícita da guarda de dados em
`/usr/libexec/muos-boot/card-guard.sh`. O pacote de boot já depende da sessão;
a sessão não deve precisar dele para montar ou desmontar seus dados.

O pacote C22 passou no host e no R35S, no mesmo boot43. Uma sessão com
`muos-boot` oculto no namespace privado carregou volume55/brilho70, atingiu
first paint com supervisor, confirmou software0.55/backlight70 e parou limpa.
A guarda e a desmontagem funcionaram sem importar código do coordenador.
Não houve instalação de novos componentes no cartão, reboot, novo token ou
repetição da edição física C21. O original dArkOSen32 permanece preservado.

## Alterações

- `preferences/data-functions.sh` exige que o chamador tenha carregado
  `diag_card`, retornando64 antes das verificações de hardware se a função
  estiver ausente. O worker C11 já carrega sua própria guarda. Não há novo
  source durante as verificações de identidade ou cleanup.
- O diagnóstico C20 e seu executor foram ajustados para levar e carregar
  `card-guard.sh` no próprio pacote. Isso mantém o chamador compatível, mas o
  diagnóstico antigo continua hardcoded60/75: NÃO executá-lo no cartão55/70.
- A receita gera `payload.sha256` com os15 componentes imutáveis do runtime.
  Start com `preferences_enabled=1` exige manifesto regular e hashes válidos
  antes de criar uma geração ou iniciar o worker. Stop/status continuam
  disponíveis; serviço desabilitado e ramo legado0 preservam o comportamento.
- A receita declara `util-linux`; o Kconfig exige basic binaries e mount,
  cobrindo findmnt/flock/blkid e o mount real usados pelas guardas. Core/profile
  continuam fornecendo as demais dependências já declaradas.
- O preparador valida cobertura exata e relativa do manifesto, reinstala a
  receita para conferir que o manifesto não muda, verifica ELF/loader/sintaxe
  BusyBox e exige o baseline do SDK antes/depois. Não recompila a imagem inteira.

Nenhum código upstream foi copiado para essa correção. Os scripts novos são
MIT. Foram consultados o contrato de inicialização muOS, as receitas do port e
Config.in/util-linux.mk do Buildroot local. A guarda de cartão MIT já existente
continua recusando o original32 e exigindo identidade/tamanho do teste128.

## Verificações

Oito fixtures isoladas passaram sem pacote de boot ou hardware: disabled sem
manifesto; recusas64 de manifesto ausente/symlink, helper alterado e executável
ausente antes de criar geração; start/status/stop com pacote válido; função de
guarda ausente recusada antes do hardware; guarda local disponível.
Stage: runtime-session/package-checks.cbtgsds4.

A macro real de compilação/instalação passou, seguida da reinstalação com
manifesto idêntico. A cobertura inclui8 scripts,6 ELF e profile-source.sha256.
Os seis ELF são byte a byte iguais aos do C21 nativo: comparação contra o
arquivo de deployment antigo cujo SHA está no manifesto C21 congelado.
Stage: runtime-session/service.wjbd9ueq.

O primeiro harness de reinstalação usou um alvo phony cujo $(@D) virou `.` e
não encontrou os binários. Isso ocorreu somente no staging do host. Corrigido
para um alvo dentro de recipe-source; compilação e reinstalação seguintes
passaram. Stage de falha xffpqo6s retido; sem efeito no cartão ou SDK baseline.

Quatro casos no Kconfig REAL do Buildroot, com output separado, passaram:
sessão desabilitada por padrão; opt-in sem pacote de boot; ausência de mount
ou basic binaries impede selecionar a sessão. Nenhum .config do SDK foi
alterado. Stage: runtime-session/package-kconfig.xvadgj0s.

## Ensaio nativo específico

O executor ganhou `--operation package-isolation`, com uma única sessão sob
lease90. O helper de diagnóstico cria namespace privado, monta um diretório
RAM vazio sobre muos-boot e inicia o serviço. O worker clona esse namespace;
o pai retira apenas seu próprio bind. A prova verifica simultaneamente que a
guarda de muos-boot está ausente no worker e presente no namespace global.

A sessão boot43/run-0002 passou com o novo manifesto e a guarda local:
55/70 carregados/aplicados/checkpointados, stop/restore result0, raiz privada
e globalRO, hashes de configurações/slots/ALSA e mixer/DRM restaurados.
Pacote/helper/diretório RAM removidos; p3 desmontada, mountinfo global idêntico,
brilho80, root0755, taint0, rede,55 hashes e assinaturas kernel/storage0 ao final.
Stage: preferences/session-native.jt2b3og7.

Provas públicas congeladas com SHA256SUMS:

- dist/phase4/session-package-independent: pacote, manifesto, oito fixtures,
  receita/reinstalação, equivalência de ELF, fonte e ensaio nativo limitado.
- dist/phase4/session-package-kconfig: quatro casos do Kconfig e fontes do teste.

C21 físico e reboot42→43 não foram repetidos; seus proofs permanecem intactos.
Este ensaio se justifica pela alteração no caminho da guarda e no gate de start.

## Próximo incremento e limites

O pacote está preparado e validado para compor o próximo candidato, mas o
rootfs completo ainda não foi reconstruído/testado com esta receita. O manifesto
local cobre o runtime; não substitui o perfil C10/21, a infraestrutura da imagem
ou o manifesto final de pré-requisitos. O deployment ainda carrega um manifesto
histórico de fundação para ferramentas antigas; o ensaio usou explicitamente os
55 hashes instalados. Não tomar esse arquivo histórico por aprovação de uma
nova composição inteira do firmware.

Próximo: compor e conferir o candidato de rootfs, manifests e defaults após
pacotes/overlays, antes de desenhar a instalação e o ensaio de boot de uso único.
Manter `enabled=0` e `preferences_enabled=0` nos defaults. O C12 antigo continua
inativo/sem.once/allow_power0; não rearmá-lo nem habilitar menu permanente.
Um futuro teste de boot deve ter seleção e recuperação C07 próprias, explícitas.

O par salvo continua55/70; o diagnóstico restaura brilho80 fora da sessão.
Power/suspend/fones/calibração/longa duração e perda elétrica durante commit
continuam não qualificados. O Steam Deck continua fora do fluxo e já limpo;
o backup privado640MiB permanece apenas no host, sem ser exportado nestas provas.


A composição seguinte foi executada em [C23](phase4-rootfs-candidate.md):
rootfs privado512MiB no host, fundação89 recalculada após macros/hooks, correção
do bootstrap para template C10 passivo e contador de fábrica, fsck/releitura/ABI/
loaders e14 recusas passaram. Não houve instalação nem boot desse candidato.
