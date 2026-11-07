# C49 — Game Boy com conteúdo privado

Incremento de02/11/2026 no C07/boot68/IP192.168.15.14:2222. Usa o Gambatte
GPLv2 já preparado noC48, sem recompilar core/host/SDK, instalar arquivos ou
reiniciar o aparelho. A ROM privada fornecida pelo usuário foi executada em
memória; conteúdo, imagens, áudio bruto e estados não integram a prova pública.
Original32 dArkOSen e Steam Deck continuam fora do fluxo.

## Implementação

`phase4-gb-core-check.c` carrega o core com RTLD_NOW e a ROM em memória, confere
o checksum do cabeçalho, API1 e RGB565, roda conteúdo com Start/direcional
sintéticos e verifica vídeo/áudio não zero/poll/estado de memória restaurado.
Reset/descarregamento também são exercitados. Sem SDL/GPU/ALSA no teste API;
não infere posição de Mario a partir de endereços de RAM específicos do jogo.
O bootloader externo fica desabilitado no harness; diretório system vazio.

`check-phase4-gb-core.py` usa a cópia original ignorada peloGit, sem gerar ROM
ou alterar seus bytes. Hash e recibos completos ficam somente em build/.
Stage APIapi.hnkaejde e nativecycle.c7l1qqdr produziram os mesmos dados:
615frames,160x144/RGB565,337713frames de áudio,234899nãozero, pico12871,
32768Hz/59,727501fps e615polls/states, reset/serializeRAM aprovados. Isso
comprova a API e callbacks; a jogabilidade física é observação separada.

`gb-core/app-launch.sh` mantém as guardas do C47: cápsula root700, manifesto
root600 com exatamente core.so/private.gb, nomes/digest/modo/tipo/nlink, mídia
tmpfs, recusa a symlinks e conteúdo preexistente. Copia somente para
/mnt/mmc/ROMS/GB/private.gb emRAM, compara os bytes e usa o host C47 com
--fresh/--diagnostic-content/--diagnostic-seconds=45. Achievements/netplay do
host continuam desabilitados pelo modo diagnóstico. Nenhum save é persistido.

`gb-core/session.sh` tem três percursos: API nativa supervisionada25s,
gráfica automática45s, ou seleção nativa pelo app com marcador físico próprio
root600/consumo único. Gráfica tem supervisor65s; captura perf nativa e CSV
limitado antes da restauração. `select.sh` é o selectC47 normalizado exatamente:
retira o ramo de guardasNES não usado e altera apenas prazo30→45/owner50→65.
Mantém menu120s, A nativo, quarentena governor/controller e launcher20s.

WorkerC46 byte-idêntico, owner210/externo240, /run/muos e /tmp privados,
root/prefs/sysfs protegidos, MUOSDATA ro,noload e preferências voláteis55/70.
Falha/sinal/rollbackC45 e parser/loaderC47 foram reutilizados por hashes, sem
reexecutar provas aprovadas ou modificar refs. O controlador confere build/API,
8guardas do launcher/11de sessão e API nativa antes da gráfica. A observação
exige perfil anterior do mesmo boot/core/ROM/host com pelo menos58,5fps.

## Evidências e observação

Guardas locais checks.eqhcv_qh (8): manifesto adulterado, ROM ausente/symlink,
mídia persistente, destino já existente e symlinkROMS, além do caminho válido.
Fixtures usam bytes sintéticos, nunca a ROM comercial. dispatch-check.3erh1hq4
(11): dispatch automático/físico, marcadores inválidos, erro do app, CSV
ausente/symlink/grande e execução duplicada. Elas não emulam o jogo. A API
nativa foi verificada separadamente em cycle.c7l1qqdr, operação0/cleanup0.

Perfil automático profile.s1q811xh:2691frames/45s≈59,8fps, core2,222ms com
upload0,812ms incluído, apresentação14,183ms e frame16,685ms. Zero faltas e
zero frames ausentes no áudio do CSV; DRC+0,3402%. Core e SDL32768Hz, enquanto
o backend ALSA negociou48000Hz/RW/S32_LE/period1024/buffer4096. As taxas de
interfaces diferentes não constituem por si só uma falha: PipeWire faz a
conversão. Foi medida a taxa física durante a rodada seguinte.

Rodada observe.6at5n4_r: menu comprovadamente ativo (C46_APP_PRESENT serial20 e
processo muxfrontend) antes da pergunta. Usuário instruiu apenas A/Start/D-pad,
com A opcional no jogo, sem Power/volume/brilho, e respondeu **“Deu tudo certo!”**
à conferência de imagem, controles e áudio limpo/audível. Registro físico
preservado; não há declaração explícita separada do retorno visual. O retorno
ao launcher foi conferido pelos recibos técnicos: serial20→84, saída normal,
app_status0. O jogo entregou2690frames/45s≈59,78fps, zero faltas/frames ausentes
noCSV e DRC+0,3588%. Operação0/cleanup0, rootRO/fundação97/taint0/prefs55/70,
mounts globais e infraestrutura preservados. PCMclosed, sem processos de UI,
áudio ou input residuais; cápsula/ROM/ELFs RAM removidos e página finalC49.

Dois snapshots somente leitura durante o jogo mantiveram o mesmo PCM owner e
taxa declarada48000: hw_ptr/tstamp mediram48000,49frames/s, sem alteração de
IRQ, quantum, codec215 ou volume salvo55. Essa medição e a resposta física
qualificam o ensaio curto; não substituem teste prolongado ou após novo boot.

Janelas perf têm no máximo1024amostras e stages aninhados se sobrepõem.
Frames/45 usa o prazo do diagnóstico, não timestamps de cada frame do painel.
Não generalizar esta aprovação a outras ROMs/cores, persistência ou NES:
o limite de desempenhoC48 continua aberto.

## Fontes fixadas e preservação

[Gambatte Libretro](https://github.com/libretro/gambatte-libretro), commit
77f2567d718b8973d02caa2daa8dce4953faf811, GPLv2/COPYING/fontes retidos em
gb-core/build.lgsx_3c2 e cache. ELF SHA
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57.
HostC47host._t02eefb SHA
2ba1ca32d2e3c7c9157d07043ecab26a8ef0913871dca0400fe57b66b92d7bc1.
UI/libC46build.srarmig3 e runnerC44 preservados. ROM permanece em port/roms/gb,
ignorada peloGit; não incluir em dist, imagens ou pacotes. Prova pública deve
usar lista permitida de marcadores/relatórios sem ROM ou buffers comerciais.

Próximo incremento: manter esse caminho como base de conteúdo privado e
implementar saída voluntária do jogo com hotkey já existente, usando ações
reversíveis e retorno supervisionado. Saves duráveis exigem incremento próprio;
não habilitar Power, instalação permanente ou novo boot por rotina.
