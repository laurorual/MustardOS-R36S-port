# Fase 4 — C05: primeiro áudio no kernel próprio

**Estado: C05 aprovado no recorte de três bipes, com rota SPK_HP.**
Revisão5, BOOT0012: usuário confirmou “Agora sim ouvi. Tudo certo”. Coleta
e análise passaram: PCM S32_LE/estéreo48k, ganho157, softwareunity, rota
SPK_HP; restauração de SPK/95 e software0,35, snapshot ALSA pré-core,
parada dos serviços/logger, root ro, fsck e retorno saudável ao dArkOSen.
Provas imutáveis: `dist/phase4/native-audio-route-preboot/` e
`dist/phase4/native-audio-boot/`. Falhas anteriores permanecem preservadas.
O [preflight anterior](phase4-native-audio-preflight.md) permanece uma prova
histórica somente de host. Esta continuação integra boot/cleanup e coleta.
Recorte: core/input com PipeWire/WirePlumber, três bipes de 3 s, sem UI,
hotkeys ou rede. Kernel `4.4.189-muos-r35s-p4`, somente R35S/Panel 0.

Isso não aprova frontend sonoro, volume final calibrado, fones, áudio
prolongado, energia ou rcS completo. O perfil persistente ainda é95/SPK;
a rota audível e o ganho foram temporários. A próxima integração deve
usar explicitamente a rota validada e testar o áudio real dos menus.

## Decisão de ganho e evidência

Na leitura SSH desta rodada, dArkOSen saudável: Image original inalterado,
taint 0, cinco contadores Btrfs 0, ES/ogage/Fn ativos. Playback Volume
`95,95`, escala `0..237`, Playback Path SPK_HP. O usuário confirmou áudio
conhecido audível e disponibilidade para a troca/teste.

O perfil candidato já contém Playback95 e rota SPK. O probe exige ganho95
antes de tocar; não eleva ao máximo nem inventa conversão para dB. Usa o
WAV conhecido (`959fcac2…c43e8`, S16/stereo/48kHz, três bipes/3s), com
software em unity apenas durante o diagnóstico; guarda e restaura o valor
lido por wpctl. Isso não altera o preset persistente35 ou habilita hotkeys.
Ausência de som ou volume baixo serão resultados separados do status do
player; calibração final do speaker continua necessária se percebida baixa.

## Ordem e cleanup

[Hooks](../../port/device/rk-r35s-p0/audio-diagnostic/session.sh) são chamados
antes de S95, depois de S05/udev/D-Bus/storage. Salvam o estado ALSA daquele
boot, copiam o perfil para /run e fazem bind temporário de perfil/config
core audio1/input1. O arquivo persistente segue audio0. S95 inicia o stack
nativo, valida sink e mantém o input/mapping já testado.

[Probe](../../port/device/rk-r35s-p0/audio-diagnostic/probe.sh) e
[política](../../port/device/rk-r35s-p0/audio-diagnostic/functions.sh):
marcador C05/kernel/root/core prontos, UI ausente, sink RK817 correto;
Playback95 antes/durante; aplay limitado a12s, amostragem de hw_params,
controles, software e logs. Player/sampler são esperados antes do retorno;
falhas de player/sink/ganho/PCM reprovam. Restore de software também é
tentado no EXIT. Limites dependem do progresso do kernel; não garantem
cancelar I/O bloqueado no driver.

Depois do probe, cadeia é parada em ordem inversa. Cleanup tenta também
S80 stop caso S95 tenha falhado antes de publicar áudio pronto; processo
residual força falha e limpeza por nomes do runtime próprio. Remove binds,
restaura ALSA anterior ao core e compara `amixer contents`. Só depois há
sync/root ro e gravação DIAG07/BOOTnnnn, preservando DIAG04–06.
Nenhum cliente dArkOSen está presente nesse boot; original32 fica guardado.

Evidência upstream: `refs/muos/internal/script/init/S80pipewire.sh:455–461`
restaura configurações ALSA/perfil; `:483` aplica volume salvo;
`:565` inicia parada. Não presumir que startup preserve rota/mixer.
`usr/libexec/muos-core-lifecycle` retorna cedo se ready já existe, por isso
configuração deve anteceder S95. O perfil asound é bind temporário para que
o store nativo não regrave a cópia persistente. Configurações ALSA comuns
podem ser restauradas pelo S80 na raiz candidata, como esperado pelo native.

## Preparação e guardas

[Preparador](../../port/scripts/prepare-phase4-native-audio.py) parte do C04
host sem seed; nenhum binário foi recompilado nem Debian importado. Auditoria
shell/QEMU/loader/ext4/fsck passou. Cinco fixtures da política cobrem sucesso,
player falhando, sink/ganho errados e PCM fechado, com restauração de volume.
Duas fixtures dos hooks cobrem ciclo normal e falha no segundo bind,
verificando remoção de binds e tentativa de restauração ALSA.

Installer atual exige C04 e hashes da política/core/S80/plugin/perfil.
Somente seis arquivos de diagnóstico/dados, bootstrap guardado primeiro e
marcador C05 por último. Exceção de tamanho somente para WAV576044 e hash
fixo; os demais assets mantêm limite128KiB. Diretório novo é restrito a
/usr/share/muos-diagnostic. Backup só de código/config, nunca seed.
Kernel/DTB/U-Boot/tabela e bibliotecas preservados. Guardas de CID/capacidade,
PartUUID, root candidato desmontado, Image/taint/Btrfs continuam obrigatórias.
Rollback existe, mas não foi testado com queda de energia física.

Não clonar raiz viva nem ler/copiar/hashar seed. Depois da instalação,
congelar prova pré-boot, confirmar fsck/saúde e só então desligar normalmente.
No boot, tela avisa e espera5s antes dos bipes. Observar desde power-on,
sem botões, esperar AUDIO/INPUT OK + root ro + DIAG07 salvo. Registrar falha
literalmente; não repetir para substituir o resultado. Retornar ao original,
coletar em FAT ro/namespace privado e conferir audibilidade/PCM/restore/fsck
antes de declarar aprovação. Não aprova frontend sonoro, hotkeys, shutdown,
rede, conteúdo, outros painéis ou estabilidade prolongada.

## Falha física e coleta ampliada

O usuário relatou duas tentativas com `Root remount ro failed` e nenhum
bipe. O runner original interrompe antes de criar DIAG07 nesse caminho;
o report estava em /run e não foi preservado ao desligar. Causa ainda não
identificada: investigar processos/FDs/mmap graváveis e montagens, sem
atribuir a PipeWire ou ao driver antes de evidência. Não inferir que o
player chegou a iniciar.

Naquela etapa, o usuário retornou ao dArkOSen. A revisão seguinte
registrou todos os processos e FDs/mapeamentos compartilhados
graváveis da ext4, tenta root ro e preserva logs FAT mesmo se a tentativa
falhar. Status continua1 e a tela informa root rw/log salvo; nenhum caso
com raiz rw será aprovado. Helper lê somente metadados procfs, sem bytes
ou hashes de arquivos privados. Deve ser testado no host e passar nas
guardas/preimages C05/fsck antes da próxima rodada física.

## Diagnóstico confirmado: logger e identidade ALSA

A revisão de observabilidade confirmou mulog PID590, FD5 gravável em
`/opt/muos/log/2026_10_26_S80pipewire.log`, e root ro recusado como busy.
Fonte `refs/muos/frontend/module/mulog.c:713` só faz saída por idle quando
modo debug/verbose está desligado. Encerramento por SIGTERM executa
flush/close do cache em `:720`. Revisão2 encerrou o logger depois dos
clientes: C05_LOGGER_STOPPED=1, zero FD/mmap graváveis reportados, ROOT_RO1,
FAT desmontada e fsck offline0 sem aviso de journal. Essa causa está
resolvida; áudio continuou reprovado. Provas separadas:
`dist/phase4/native-audio-writer-diagnosis/` e `native-audio-logger-stop/`.

No BOOT0009, S80 abriu o socket PipeWire, mas esperou em vão pelo sink
`alsa_output.platform-rk817-sound.playback.0.0`; probe não foi iniciado.
O grafo mostra `alsa_card._sys_devices_platform_rk817-sound_sound_card0`,
`api.alsa.use-acp=true`, apenas uma source `stereo-fallback` e nenhum sink.
Udev card0 tem SOUND_INITIALIZED1, porém não ID_PATH. O dArkOSen, lido por
SSH, tem `ID_PATH=platform-rk817-sound` na mesma placa.

As regras eudev78 marcam SOUND_INITIALIZED, mas saem cedo para plataforma
antes de importar path_id; a regra60 importa o path apenas em controlC*,
não em card*. Consequentemente o nome sysfs não combina com a regra
específica do `core-wireplumber.conf` e ACP não é desativado. Não trocar o
sink esperado por um nome arbitrário nem desativar ACP para todas as placas.

Correção em preparação: regra própria79 só para card ALSA cujo ancestral é
plataforma/rk817-sound, usando IMPORT{builtin}=path_id. Fonte primário
`eudev-3.2.14/src/udev/udev-builtin-path_id.c:621–625` produz a identidade
platform a partir do sysname. O grafo ativo será capturado para conferir
que a regra específica aplicou ACPfalse e publicou o sink correto. Não
alterar ganho, kernel ou DTB junto dessa correção.

## Enumeração resolvida; teste ainda inaudível

Revisão3, `audio-enumerate.cmak5i25/boot4`, BOOT0010: ID_PATH da card0 agora
platform-rk817-sound; grafo com alsa_card.platform-rk817-sound, ACPfalse,
sink esperado e PCM real S32_LE/stereo/48000, period512/buffer2048. Software
0,35→1,00→0,35, Playback95 durante, rotaSPK, Headphone Jackoff, aplay0,
root ro/parada/fsck aprovados. **Usuário não ouviu nada**: isso não aprova
reprodução audível. Prova `dist/phase4/native-audio-pcm-inaudible/`.

Próxima hipótese é atenuação do DAC, não afirmada como causa antes do teste.
Revisão4 usa 157,157 apenas durante os bipes e restaura95 com cget de
readback; não altera o perfil persistente95 nem o presetsoftware35. Limite
reportado pelo próprio driver é237; 157 é inferior e próximo dos ganhos
153–157 usados em ensaios anteriores no kernel instalado. Isso não transfere
aprovação ao novo BSP. Mantém a rotaSPK e o mesmo WAV, isolando o ganho.
Os únicos ganhos aceitos pelo probe são95 ou157; nunca há ajuste ao máximo.

Quatro fixtures de ganho cobrem sucesso, player falhando, PCM fechado e
falha ao aplicar softwareunity. Todas conferiram restauração de codec95 e
software0,35. Restore é tentado no retorno normal e no EXIT; falha invalida
o resultado. O cleanup do core ainda restaura o snapshot ALSA pré-core.
Nova prova física e conferência de restauração/saúde são necessárias.

## Ganho157 insuficiente; referência stock e rota em comparação

Revisão4, BOOT0011, coleta `audio-gain.39qzpnz_/boot5`: mesmo PCM S32_LE,
estéreo48k, period512/buffer2048; amixer amostrou157,157 durante o playback,
95,95 depois; software0,35→1,00→0,35, rotaSPK e Jackoff. Player0, probeOK,
parada/logger/rootro/fsck/saúde passaram. Usuário: “não ouvi nada”. A prova
`dist/phase4/native-audio-gain-inaudible/` mantém áudio não aprovado. Isso
refuta apenas que elevar até157 seria suficiente nesse caminho; não mede
sinal elétrico nem exclui diferenças de driver/clock/rota/formato.

O mesmo WAV foi tocado no dArkOSen usando o default/dmix existente, sem
parar serviços ou alterar mixer. Usuário ouviu perfeitamente na repetição
(primeira audição prejudicada por ruído ambiente). PCM S16_LE/44,1k,
SPK_HP/95. Referência registra codec, I2S e clocks durante a reprodução.
A tentativa inicial de captura não chegou ao player por PATH de runuser;
correção de caminho absoluto passou, temporários removidos.

No driver compilado, `sound/soc/codecs/rk817_codec.c:558–585` configura SPK;
`:620–647` também habilita estágios HP/charge pump em SPK_HP. São caminhos
analógicos diferentes, não equivalência presumida a partir dos nomes.
Os dois DTBs comparados mantêm hp-volume20/spk-volume3, sem GPIO opcional
hp-ctl/spk-ctl. Avisos de widgets DAPM ausentes permanecem no log e ainda
não foram atribuídos como causa da ausência de áudio.

Revisão5 mantém ganho157, backend e formato anteriores; só muda a rota para
SPK_HP durante os bipes e restaura SPK/95 por readback. Capturas debugfs são
somente dos mapas legíveis codec0x00–0x4f/I2S e clock_summary; não escrevem
registros, não leem mapa geral do PMIC ou seed. Montagem debugfs criada
pelo probe é removida no EXIT. Oito fixtures verificaram sucesso, player,
PCM fechado, aplicação de software/rota/ganho e falhas transitórias dos
restores. Falha de restore reprova mesmo que o EXIT consiga reparar depois.
Instalação de três scripts, preimages, QEMU/shell/fsck/saúde aprovados;
prova `dist/phase4/native-audio-route-preboot/`. O teste físico está abaixo.

## Revisão5 audível: evidência e limites

Coleta `build/phase4/linux-diagnostic/audio-route.9tz8v3zh/boot6`,
DIAG07/BOOT0012, `C05_DIAGNOSTIC_STATUS=0`. O usuário confirmou os bipes e
o resultado correto na primeira tentativa dessa revisão. A classificação
positiva inclui a audição; BOOT0010/0011, também status0 porém inaudíveis,
continuam classificados como falha de audibilidade.

| Verificação | Evidência no report/análise |
| --- | --- |
| Sink/placa | ID_PATH platform-rk817-sound; ACPfalse; sink alsa_output.platform-rk817-sound.playback.0.0 |
| PCM durante | MMAP_INTERLEAVED, S32_LE, estéreo48000, period512/buffer2048 |
| Controles durante | Playback157,157; Playback Path3/SPK_HP; Headphone Jackoff; software1,00 |
| Restore do probe | path-restored1/SPK; codec-restored95,95; software0,35 igual ao snapshot inicial |
| Restore do core | amixer contents pré-core/restaurado iguais; binds temporários removidos |
| Registros/clocks | HP CFG0=0x80, HP CP=0x11; I2S MCLK12,288MHz; snapshots somente leitura |
| Fechamento | C05_DEBUGFS_RELEASED1; C05_LOGGER_STOPPED1; nenhum writer da raiz; ROOT_RO1 |
| Regressão C02 | seed persistido/rotação nativos, RNG pronto6814ms, udev depois; apenas aviso conservador do próprio seedrng |
| Retorno stock | Image original31bdb671…b0577, taint0, cinco contadores Btrfs0, ES/ogage/Fn ativos; fsck candidato0 |

Código próprio relevante: `audio-diagnostic/functions.sh:60–70` troca a
rota antes do ganho; `:37–49` restaura rota antes do ganho, com readback;
`probe.sh:30–47` faz cleanup e remove debugfs criado pelo probe. O preparador
gera o probe da revisão5 com SPK_HP/157/debug1; os defaults do arquivo fonte
não substituem os hashes/assets da revisão instalada.

**Fato:** SPK ficou inaudível em95 e157; SPK_HP ficou audível em157 com o
mesmo WAV/PipeWire/PCM. A ativação dos estágios HP é coerente com o código
do driver. **Hipótese:** o caminho físico do speaker requer esses estágios
nesse hardware. Não houve medição elétrica ou teste isolado da rota HP;
não inferir uma regra para todos os R35S/R36S ou copiar o quirk mainline.

Comparação somente leitura com stock está em `hardware-comparison.json`:
estágios analógicos observados coincidem na reprodução audível; diferem
volume DAC e largura PCM. Stock mostrou cget95 e registradores DAC0x70;
candidata157 e DAC0x62. Portanto nem números de mixer iguais estabelecem
ganhos físicos iguais entre esses drivers. Não há calibração de dB/loudness.
Usuário confirmou audibilidade; volume confortável e ausência de cortes
não foram quantificados separadamente (campos *_confirmed=false na análise
significam ausência dessa confirmação específica, não uma falha relatada).

Nenhuma mudança em kernel, DTB, U-Boot, módulos ou bibliotecas nesta revisão.
Nenhum material de seed foi lido/copiado/hashado; somente metadados públicos.
Temporários removidos, candidato desmontado e SSH encerrado. Console
permanece no dArkOSen; nenhuma gravação, build ou teste crítico em andamento.

**Próximo teste mínimo:** frontend supervisionado C04 com áudio S95/S80,
rota SPK_HP e ganho limitado explicitamente, preservando o fechamento C05.
Primeiro sem hotkeys: navegação, A/B/Fn, submenus e drenagem do último som;
substituição diagnóstica da ajuda somente se necessária e documentada.
Depois volume/brilho em rodada separada. Integrar perfil/cache de board
coerentes no candidato; não assumir que o perfil persistente95/SPK atual
já reproduza o recorte aprovado. Não reutilizar binários de outro rootfs.
