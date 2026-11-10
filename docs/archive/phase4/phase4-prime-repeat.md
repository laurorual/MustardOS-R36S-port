# C39 — repetibilidade do áudio após reboot

## Ensaio executado

Motivo concreto: C36 tinha um único primeiro menu após reboot qualificado (62);
sessões quentes anteriores tinham escondido a falha. Nenhuma configuração,
instalação ou calibração nova foi aplicada. Partimos do C07/63 real, PCMclosed,
raizRO e taint0, para um novo pedidoC25 e lease180. Stage:
`build/phase4/rootfs-candidate/c25-physical.imisykay`, esperado64/fallback65.
Pedidos de arm/reboot foram despachados uma vez, com recibos próprios; C12off.

Boot64 abriu menu pelo ajuste instalado: prime PCM, IRQ/RW, ganho215,
quantum1024,55/70 e ambas raízesRO. Antes de pedir audição, medimos
44101.067174frames/s para44100 declarados, mesmo owner/trigger. Usuário confirmou
“Imagem e navegação normais; som limpo e audível”. Após navegação:
44100.797953frames/s, sem override manual. Há agora dois primeiros menus após
reboot qualificados (62 e64); isso não qualifica coldboot/longa duração/fones.

Lease/coleta64 passaram0 com mixer/DRM/caches e brilho80 restaurados,
prefs55/70 preservados e processos de infraestrutura idênticos. Retorno65/C07
solicitado uma vez e aprovado: rootRO0755/97hashes/taint0/rede/erros0/FAT+p3
desmontadas, semUI/PCM/token. RAM e relatórios duráveis naFAT coincidiram.

## Provas de repetição sem sobrescrever histórico

O empacotador aceita --repeat-proof só para uma repetição positiva do prime.
Confere SHA256SUMS das provas originais62/63, o MESMO plano instalado e avanço
do contador. Usa números reais no nome, recusa destino existente e trial antigo.
As provas novas guardam hashes das referências e os checks do empacotamento.
8fixtures host passaram; tentativa real de empacotar o trial62 como repetição
foi recusada antes de criar qualquer artefato público. Não houve novo SSH por
esse teste do empacotador.

Provas desta rodada: `dist/phase4/primed-launcher-boot-0064` e
`primed-launcher-fallback-0065`, ambas com SHA256SUMS conferidos. Sem imagem, raw áudio,
backup privado, seed, chaves ou credenciais. Provas anteriores imutáveis.
Original32 e Steam Deck preservados. ImagemC38 e políticaC36 não mudaram.

## Continuação

[C40](phase4-libretro-smoke.md) prepara core sintético original e valida seu
contrato no SDK/QEMU. Antes de executá-lo no R35S, integrar hostmuxretro,
no-content e ciclo de vida/limpeza dos descendentes. Não repetir áudio, USB,
calibração ou flash como pré-requisito sem nova razão concreta.
