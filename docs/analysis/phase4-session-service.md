# Fase 4 — C11: ciclo independente da sessão

Serviço privado com start/status/stop, consumindo o perfil C10 sem carregar
executores/helpers C06/C09. O ensaio mantém instalação atual e SSH; pacote
só em RAM. Habilitação permanente e contrato de persistência são incrementos
separados. Ciclos nativos aprovados no recorte descrito ao final.

## Evidência e escopo de serviços

Upstream internal/script/init/sysinit inicia udev/D-Bus, áudio e S99, e adia
outros serviços até first_paint. script/init/shutdown percorre serviços em
ordem reversa. S99muos.sh também chama swap/IRQ/checkmsd/control/catalogue,
que não foram aprovados juntos nessa candidata. Buildroot rcS/rcK executam
todos os S?? em ordem direta/reversa e não coordenam ownership da sessão.

O C11 assume somente S30dbus-daemon → S90muos-storage → S95muos-core →
S96muos-input-ready → S99muos-ui. Marca cada tentativa antes de iniciar;
parada percorre a lista reversa mesmo após erro, incluindo início parcial.
Não inicia/para udev, rede ou SeedRNG. Consulta RNG atual sem recarregar seed.
Recusa D-Bus/core/storage/input/UI já ocupados. Primeiro frame novo e
supervisor/parent do frontend devem ser conferidos antes de anunciar ready.

## Interface e processo

port/device/rk-r35s-p0/session/service.sh implementa start/status/stop;
S98muos-session é adaptador de init. Defaults enabled0/lease180s, sem autostart.
MUOS_SESSION_CONFIG permite config root-owned0600/0644 de teste em RAM.
Lease aceita30..600s. Start cria geração run-NNNN, inicia worker independente
com setsid e namespace privado; CLI retorna após ready. Start já ready é
idempotente, sem novo PID ou novo prazo. Status exige PID/starttime/cmdline
da geração e ready. Stop verifica identidade antes de TERM e espera cleanup;
PID reutilizado/estado sujo não permite sinalizar outro processo. Sem KILL
forçado do worker; prazos de chamadas e controle são limitados.

worker.sh exige PID1BusyBox/kernel4.4.189-muos-r35s-p4/Panel0/ext4 e cartão
128 conhecido, recusando o cartão original. Trata-se de guarda de bancada,
não autodetecção ou serviço genérico para outros cartões/painéis. A lease
encerra a sessão quando expira; SIGTERM da CLI também passa pelo mesmo cleanup.
Configuração/volume durante a sessão são transitórios: usuário não deve
esperar persistência entre duas gerações. Cada start aplica o perfil C10.

## Perfil, mounts e saída

Manifesto congelado do perfil é conferido antes de consumir seus dados.
Config/device-config/share-volume recebem cópias RAM; defaults/asound/hotkeys/
WAVs recebem binds privados. Os21 hashes ativos são checados antes de iniciar
core/helpers. Config UI0 do perfil é substituída somente na cópia da sessão
para S99start. Os setters podem regravar valores semLF; esse comportamento
foi documentado no C10 e não invalida o manifesto inicial.

Worker usa rootrw apenas no namespace privado; SSH continua no mount ro.
Snapshot ALSA/backlight/DRM,21 hashes originais e pasta de volumes são
restaurados. Saída para a UI, core/input/áudio/storage/D-Bus, remove binds,
reconstrói cache e encerra o mulog próprio. Mantém3s de graça antes de parar
UI, igual ao recorte sonoro já validado; não é medição universal de drain.
Confere ausência de processos, root-writers e remountro/taint0. Logs/result/done
ficam em /run/muos/session por geração. Coletar só whitelist, nunca cópias
inteiras da config ou /run, rede privada, seed ou chaves.

## Receita e verificações no host

Pacote muos-r35s-session depende de muos-r35s-profile e libdrm. Compila seus
cinco utilitários MIT: namespace, bounded, rng-ready, root-writers e DRM probe,
no SDK AArch64/Cortex-A35 fixado. Loader/QEMU usa as libs da candidata;
nenhum binário Debian é reutilizado. Script adaptador/default disabled0 é
instalado pela macro SysV. Fragmento phase4-session.fragment é opt-in.

Oito casos de cadeia e dez de controle passaram: rollback por estágios,
status/stop com erro, idempotência, restart com geração/PID novos, recusa de
PID alheio, estado sujo, leases inválidas e falha125 do namespace. Fixtures
são isolados, sem rádio/hardware. Macro real de compilação/instalação foi
exercitada em harness; Kconfig/parse em output separado confirmou perfil e
libdrm. Não houve build de todas as dependências ou imagem inteira.

## Menor ensaio nativo

Duas gerações no mesmo boot: primeira com lease120s, confirmação do menu e
parada explícita; start repetido precisa manter PID/geração. Segunda com
lease30s, confirmar menu reaberto e aguardar encerramento autônomo. Consultar
status depois de cada stop, comparar infraestrutura e restauração, e manter
SSH ativo. Sem troca de cartões, reboot ou código persistente novo.

Mesmo após aprovação, o rcS completo permanece fora desse recorte: ele
iniciaria serviços anteriores ao S98, que o worker corretamente recusaria
como ocupados. Resolver essa ownership/política antes de enabled1 permanente.
Persistência real, Power/suspend, áudio máximo/escala de brilho e warmbootWi-Fi
continuam pendentes; recuperação física da rede C07 segue disponível.


## Resultado nativo

Stage service.f5dx49ft, mesma candidata/BOOT0025. Ciclo1: start/status0,
repetir start preservou PID/starttime/geração; usuário confirmou tela/sons/
navegação/submenus/ajuda. Stop explícito0 após6,19s; status3 e repetido stop0.
Ciclo2: geração/firstpaint novos, lease30 expirou e cleanup0; usuário não
viu o menu e pediu repetição. Sem confirmação visual, registro preservado.
Ciclo3: lease60 e novo worker/firstpaint; usuário confirmou “Estou vendo”,
expiração autônoma e cleanup0/status3. Não apagar/contar ciclo2 como visual.

Os21 hashes ativos e21 originais restaurados passaram por geração, mixer,
pasta de volume, brilho e DRM iguais antes/depois, cache refeito. PIDs/starttime
da rede/udev preservados, rootro/taint0/FAT desmontado/assinaturas selecionadas0,
sem processos UI/core ou socket D-Bus. Primeiro e terceiro ciclos tiveram
probesSSH enquanto ready; o monitor do segundo começou após expiração,
portanto não comprova continuidade amostrada durante toda essa janela.
Não houve fsck offline pós-boot nem reboot ou validação nova de Power/rede.

O coletor recusou o log UI acumulado586837bytes, acima de512KiB. Foi corrigido
para buscar tail196608 por SSH sem exportar o arquivo inteiro. Fonte final
limita a cópia dentro do worker pelo mesmo comando testado nativamente.
Pacote final service.o2dd7b0x passou build/loader/shell; comparação byte a byte
com pacote testado mostrou só cp→tail no worker, com restantes (cinco ELF
inclusive) idênticos. Não foi repetido ciclo GUI por alteração apenas de log.
Diff/vínculo no stage testado. Provas session-service-preflight e
session-service-native congeladas/reconferidas; fontes/artefatos/ressalvas
incluídos. Pacote/estadoRAM removidos após confirmar ausência dos workers.

Defaults da receita continuam enabled0/lease180 e o cartão C06r4+C07r3.
Próximo: definir um coordenador de boot/shutdown com ownership única e stop
antes de rede/desmontagens, além da política de configurações/logs/volume
persistentes. Ainda não habilitar o rcS completo ou serviço permanente;
o modo de bancada aplica perfil fresco a cada start e retém logs de gerações
até coleta. Rotação/retenção e persistência fazem parte dessa próxima decisão.
