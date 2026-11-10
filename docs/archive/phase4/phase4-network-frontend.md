# Fase 4 — C08: frontend com Wi-Fi/SSH mantidos

## Resultado

C08 aprovado em ensaio temporário no kernel/rootfs próprios. Usuário confirmou
menu, D-pad/A/B/Fn, Informações/Configurações/ajuda e sons na primeira sessão.
A repetição automática corrigiu somente observação/cleanup e passou com os
mesmos pré-requisitos C06/C07. Prova final `dist/phase4/network-frontend-session/`.

O analisador registrou 30 conexões SSH bem-sucedidas,
24 durante a UI, cobrindo ao menos
96.14s observados simultaneamente. Janela-alvo
nativa90s, com três segundos de tolerância antes da parada; não é medição de
drain do último efeito. Parent/first_paint novo e os PCM foram verificados.

## Integração e evidências

- `port/device/rk-r35s-p0/network-frontend-diagnostic/chain.sh` inicia/para
  somente S30dbus-daemon, S90muos-storage, S95muos-core e S96muos-input-ready.
  S99 é controlado pelo helper C06 já aprovado. Não chama S05, S10 ou C07.
- `run.sh` reutiliza `/usr/libexec/muos-c06-session` instalado, control0/nav1:
  navegação adaptada+8,8dB, confirmação/back originais e confirmação na ajuda.
  SPK_HP/Playback157/softwareunity; ALSA S32_LE/estéreo44100 observado.
  Foram mantidas as referências48/44,1k do C06, sem nova mudança de ganho.
- O pequeno launcher `port/utils/muos-mount-namespace.c` usa unshare/mount
  private/exec. O userspace não contém unshare como comando; o kernel tem
  namespaces. Probe nativo, antes de qualquer remount, confirmou namespace
  distinto do PID1 e raizro. Não houve nova biblioteca/toolchain/rootfs.
- Bind de diretórios/configuração/tema usa RAM em namespace privado. O root
  desse ensaio é temporariamente remount-rw; o ponto de montagem global do
  SSH permanece ro. Cleanup para os serviços próprios, restaura binds/mixer/
  cache e retorna o root do ensaio a ro. Uma guarda300s sinaliza cleanup se
  a execução exceder o limite ou o serviço C07 falhar.
- PID/starttime de Dropbear, wpa_supplicant, udhcpc e daemon principal udev
  permaneceram idênticos. O RNG do C07 já estava pronto: só probe não
  bloqueante, sem recarregar/rotacionar seed persistido no mesmo boot.
- Releitura dos13 hashes originais e de todos os pré-requisitos, comparação
  amixer antes/depois, DRM igual, nenhum FD/mapa compartilhado gravável em
  root e nenhum processo UI/áudio/core remanescente passaram. Taint0 e zero
  assinaturas fatais/storage selecionadas; sem exportar dmesg Wi-Fi.

## Falha do observador e limpeza de D-Bus

A primeira sessão `network-frontend.8g9d869k` terminou status1 apesar de
UI/áudio/restaurações e todos os probes SSH passarem. O snapshot final tinha
as três identidades de rede e não a linha udev. A guarda recusava qualquer
saída de pidof com mais de um PID. O relatório de processos, imediatamente
antes, continha udevd209 e worker5203; depois209 seguia vivo, PPid1/start1312.
A atribuição à guarda de múltiplos PIDs é deduzida desse código e desses
registros, não de uma captura direta da saída pidof daquela instrução.

A correção seleciona daemon com PPid1/exe correto e conserva seu PID/start.
Workers são esperados após criar/remover uinput. Sete fixtures cobrem daemon,
workers, ambiguidade, ausência e entradas inválidas, além de oito cenários de
cadeia/rollback. O script S30 nativo para o daemon mas deixa pathname de
socket; C08 agora remove somente o socket que criou, após confirmar ausência
do daemon. O antigo socket foi removido sob essas mesmas guardas antes da
repetição. Prova inicial `network-frontend-observation-failure/` preservada.

O relatório de processos pode conter comm de kernel não UTF-8. Isso é
metadado opaco; o coletor/analisador trata texto com substituição, sem
interpretar bytes como conteúdo de arquivo ou inferir corrupção de memória.

## Estado e limites

Sessão aprovada `network-frontend.c5v2x8ud`, ponteiro latest-network-frontend. Fontes,
manifestos, checks e coleta em build/phase4; provas separadas em dist/phase4.
O código C08 foi transferido somente para /run e não altera init/boot, kernel,
DTB ou bibliotecas. Credenciais, chaves privadas e seed não foram coletados,
hashados ou clonados; exportação foi por whitelist de relatórios públicos.

Manual veio da primeira sessão com mesmos componentes; a repetição foi
automática, sem pedir novamente navegação. Isso ainda não valida UI
permanente/coldboot, hotkeys/volume/brilho no kernel próprio, Power/suspend,
fones, sons originais da ajuda ou estabilidade prolongada. Não foi feito
fsck offline pós-ensaio com a raiz montada. Próximo teste: reboot normal da
candidata em estado ocioso/rootro, sem troca de cartões, para conferir
persistência da chave/RNG e reconexão Wi-Fi/SSH.

## Reboot normal subsequente — rede pendente de diagnóstico

Depois de salvar a prova C08 e remover os pacotes RAM, a verificação ociosa
confirmou rootro/taint0, rede ativa, BOOT_SEQ18 e mesma chave pública. Reboot
normal foi solicitado por /sbin/reboot. Usuário viu C07STOPPED/networkrc1/
rootro1/BOOT0019salvo; portanto a inicialização chegou ao runner, mas a
reconexão não passou. C08 não inicia automaticamente nesse boot. Sem inferir
causa ou aprovar persistência de rede antes da coleta pelo stock solicitada.
Evidência parcial `build/phase4/linux-diagnostic/network-reboot.oi45y88x`.
