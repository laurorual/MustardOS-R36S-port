# C27 — imagem integrada e calibração do alto-falante Panel 0

Atualização: [C30–C32](phase4-irq-rate-negotiation.md) instalou a política IRQ
com fundação97 e aprovação auditiva quente55, porém o áudio voltou a falhar
no56 mesmo com IRQ ativo. Fallback57/limpeza passaram; renegociação de taxa
não recuperou. Consultar o Estado atual do checkpoint antes de agir.

Atualização posterior: [C28/C29](phase4-calibrated-boot-audio-clock.md) validou
boot54 e fallback55, mas o usuário confirmou nova distorção de áudio apesar
do perfil215/quantum1024. Aprovações anteriores abaixo são históricas e não
qualificam áudio após reboot. Estado e investigação atual no checkpoint.

Concluído em 31/10/2026, no C07/boot52. O perfil instalado usa ganho de codec
215 e quantum PipeWire 1024. O usuário confirmou silêncio em 0, som limpo e
confortável em 65 e máximo limpo e adequado em 100. O par persistente de
volume/brilho continua **55/70**. A imagem privada incorpora C25 e C26 com esse
perfil; passou nos checks host, mas não foi gravada nem inicializada inteira.

## Escolha e escopo

A correção C26 já havia eliminado o chiado com quantum1024 antes da UI.
A calibração preserva essa correção e a curva cúbica nativa do `wpctl`.
Com ganho195 o máximo ainda era baixo; 205 ficou alto e limpo, mas o usuário
pediu comparar215. Esse último foi aprovado como máximo adequado. Não se
buscou o limite físico do alto-falante nem se alterou o volume salvo para
compensar o ganho. O mixer de recuperação C07 permanece no valor anterior.

O certificado próprio `port/device/rk-r35s-p0/speaker-calibration.json` registra
placa/modelo, quantum, ganho, escopo subjetivo e hash da observação real em100.
O perfil v3 referencia esse certificado; a preparação e a validação recusam
ganho divergente ou máximo sem confirmação, mesmo com manifests regenerados.
Não há qualificação de SPL absoluto, fones, música/emuladores, longa duração
ou outros painéis a partir desses efeitos de navegação.

## Ensaios físicos e limites de interpretação

Todos ocorreram sem reboot no52, em sessões C22 temporárias com lease600.
O controlador mantém cada ponto por até180s, verifica volume e ganho a cada
segundo e restaura software55 e o ganho do perfil ao terminar. A confirmação
só vale como ponto mantido quando a leitura permanece válida ao recebê-la.

| Ganho / software | Observação do usuário | Qualificação |
| --- | --- | --- |
| 195 / 0, janela inicial45s | Navegação baixa audível | Janela expirou; inconclusivo, não prova falha do mute. |
| 195 / 0, janela180s | Silêncio completo | Ponto mantido e restauração confirmados. |
| 195 / 65 e75 | Limpo e confortável | Pontos mantidos. |
| 195 / 85 | Limpo, confortável, volume usual; estimado como60% do máximo original | Comparação subjetiva, sem equivalência SPL. |
| 195 / 100 | Limpo, mas máximo baixo | Lease C22 expirou; rodada result1, não contar como aprovação integral. |
| 205 / 100 | Limpo e alto, máximo ainda incerto | Ponto mantido; retorno195/55. |
| 215 / 100 | Limpo e máximo adequado | Ponto mantido; retorno195/55 antes da instalação. |
| 215 instalado / 0 | Silêncio completo | Sessão normal sem override; ponto mantido. |
| 215 instalado / 65 | Limpo e confortável | Sessão normal sem override; ponto mantido. |

A rodada que expirou calculava seu prazo a partir da preparação do controlador,
que podia acontecer tarde em relação ao início do worker. O checkpoint recusou
a inconsistência RAM55/PipeWire100 antes de salvar preferências. O diagnóstico
preservado confirma restauração byte a byte de mixer/DRM/cache/brilho, raizRO
e ausência de gravação das preferências; não ocultar seu result1.

O prazo agora deriva do primeiro paint monotônico +570s. Cada novo ponto exige
mais de210s disponíveis para seu watchdog180s e margem antes da lease600.
As rodadas posteriores encerraram e coletaram com result0. Treze fixtures
verificam prazo, TERM, identidade, drift, limites, restauração e baseline215.

Código original: `port/device/rk-r35s-p0/volume-calibration/step.sh` e
`port/scripts/phase4-volume-calibration.py`. O runner de áudio aceita lease600;
seu default300 foi preservado. O controle continua temporário, sem editar
preferências ou habilitar menu permanente.

## Instalação nativa e recuperação

Stage: `build/phase4/rootfs-candidate/c26-update._dzvsts7`, experimento
`C27_VOLUME_CALIBRATION`; candidato `c26-source.wfwxb76w` no mesmo diretório.
O prefixo histórico c26 dos caminhos não indica ganho195.

Oito arquivos públicos foram instalados: sete existentes e o certificado novo.
Os manifests do perfil, payload C22/15 e fundação96 foram regenerados; nenhum
ELF, diretório, kernel, DTB, bootloader ou partição foi alterado. Quatorze
fixtures da transação e dez do perfil passaram. Privados, contador52 e
identidades dos daemons de rede foram preservados. SDK.config ficou intacta.

Backup privado dos sete originais:
`build/phase4/private/c24-backup.zmw_itus/original-files.tar`, modo600/pai700,
SHA256 `9594a8e843455d24e5043c1701e7ce7533a00fc40e3b4a34d06b606051213673`.
O descriptor e o plano distinguem o certificado ausente antes da transação.
Não executar rollback sobre o estado aprovado, nem restaurar backups C20
antigos que contenham estado privado/contador desatualizado.

A validação final usou `audio-buffers/session.0x_he_be`/run-0010 e
`volume-calibration/calibration.3agzv4fb`, sob `build/phase4/`. Stop/coleta0,
preferências55/70, mixer/DRM/cache/brilho80 restaurados, mounts privados
encerrados e rede preservada. O recibo `final-health.stdout` deste último stage
confirma boot52, raizRO, ganho215, fundação96, ausência de workers e erros
selecionados0. Não há sessão ou teste físico pendente.

## Composição privada

`compose-phase4-rootfs-candidate.py` parte da base C07 limpa e executa macros
reais de instalação do perfil, sessão C22, Wi-Fi-only, core/S95 e launcher C25.
Reutiliza os ELF auditados; atualiza o manifesto fonte no stage próprio antes
da instalação. Aplica o perfil pós-overlay por último e gera a fundação96
somente depois dos hooks. Não modifica refs ou o SDK.

O resultado mantém C07 como default, UI e preferências automáticas off,
contador de fábrica0/0600 em diretório0700 e nenhum token ou recibo usado.
Não contém seed, chaves SSH ou configuração privada de rede. Esse contador0
é somente da imagem de fábrica: o contador vivo52 não foi reinicializado.

Imagem ext4 de512MiB:
`build/phase4/rootfs-candidate/composition.cb2rb8ls/images/rootfs.ext4`.
SHA256: `6977d8174ec2e89f0f1a4964f1ee533d7720acd47e28b231151ed478534af826`.
O link `latest-composition` aponta para esse stage. Fsck offline, releitura
integral do inventário, raiz0755, contrato de boot antes/depois, 172 verificações
de loader AArch64/QEMU e26 casos de validação passaram. A fundação96 e o
payload15 coincidem exatamente com o alvo nativo calibrado. O bootstrap recusa
execução fora de PID1. Não é rebuild integral do Buildroot nem prova de
reprodutibilidade bit a bit ou de boot físico dessa imagem inteira.

A composição195 anterior, `composition.95gyixar`, é intermediária. Sua prova
`rootfs-c25-c26-composition` permanece histórica e imutável. A imagem final fica
privada em build, pois a redistribuição de blobs continua sem aprovação.

## Provas e próximo incremento

`dist/phase4/speaker-volume-calibration` contém fontes, checks13+14+10,
tentativas, diagnóstico da lease e coleta nativa final. A prova
`dist/phase4/rootfs-c25-c26-calibrated` contém a composição, equivalência nativa,
checks26 e relatórios. Ambos os SHA256SUMS foram conferidos; não incluem rootfs,
blobs GPU, áudio raw, backups privados ou credenciais.

Próximo passo útil: preparar a validação de boot único C25 com o perfil215 e
S95 atuais, seguido de fallback C07. O C25 foi aprovado antes das mudanças de
áudio; essa combinação ainda não teve reboot. Conferir o estado vivo e usar
o pedido C25 próprio; manter C12 inativo e menu permanente off. A imagem
inteira exige ensaio separado, sem gravar ext4 sobre a raiz viva. Original32GB
preservado; Steam Deck permaneceu fora do fluxo e limpo nesta rodada.
