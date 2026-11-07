# C48 — medição NES e preparação Game Boy

Em 02/11/2026, o console foi encontrado em C07/boot68, IP192.168.15.14:2222,
raiz ext4RO/fundação97/taint0/PCMclosed e sem sessão. As cinco sessões abaixo
terminaram com operação0/cleanup0, mounts globais e preferências55/70 idênticos,
PIDs/starttime da infraestrutura preservados e cápsulas RAM removidas.
Não houve instalação, reboot, token, escrita em preferências persistentes ou
alteração de clocks. Original32 dArkOSen e Steam Deck permanecem fora do fluxo.

## Implementação e limites

`run-phase4-nes-profile.py` usa o workerC46 byte-idêntico, seu prazo210 e o
supervisor externo240. Reutiliza as provas imutáveis de falha/sinalC45 e os
checksC47 de parser/launcher/API, verificando hashes antes de enviar os assets.
`nes-profile/profile.sh` executa a ROM original silenciosa por30s, sem seleção
ou intervenção física, e coleta o CSV nativo `MUXRETRO_PERF_CAPTURE=1` antes
da restauração. O launcher de conteúdo, core/ROM originais e hostC47 continuam
inalterados. A página final substitui o último frame estático.

O CSV oferece janelas móveis de no máximo1024 amostras; stages aninhados se
sobrepõem. A coluna core inclui o upload de vídeo durante o callback. Contagens
de faltas do CSV terminam antes do fechamento de áudio e diferem ligeiramente
da última linha do log. Frames/30 é uma aproximação pelo prazo do diagnóstico,
não timestamps de frames do painel. Hz nominais não comprovam throughput.

| Sessão privada | Variante | Frames/30s | Aproximação fps | Faltas no CSV |
| --- | --- | ---: | ---: | ---: |
| profile.yf08v2yo | C47, captura nativa | 1542 | 51,40 | 769 |
| profile.n6v405bs | primeiro hook, não ativado | 1544 | 51,47 | 765 |
| profile.9_nz67mi | callbacks medidos | 1544 | 51,47 | 767 |
| profile.6gk6ijxb | espera por software | 1574 | 52,47 | 703 |
| profile.3gmb7osf | core O3/LTO, hostC47 | 1607 | 53,57 | 640 |

Baseline: frame19,399ms, core13,506ms (upload1,695ms incluído), apresentação
5,624ms, espera de áudio0,0056ms e espera do limitador zero. Core e dispositivo
abriram a44100Hz: não há conversão48000→44100 nesta sessão, apesar dos48000Hz
do teste API que não oferece a negociação de taxa. O governor já era performance,
com leitura1296000kHz; esses valores foram apenas lidos, com sysfs protegidoRO.

Patch0013/header `phase4-core-callback-profile.h` medem os callbacks sem mudar
seus argumentos, retornos ou API. Inicialmente o gate consultava perf antes do
`perf_init`, logo não ativou: a rodada n6v405bs NÃO contém essa medida. Corrigido
para ler a opção de captura durante o carregamento. Host final host.8edb4imb,
testeQEMU callback-check.55vps9yq:5callbacks e habilitação anterior ao perf_init.
Na rodada9_nz67mi: vídeo1,7513ms/chamada, áudio0,0390ms, poll0,0006ms e
input_state0,0010ms. Essas médias incluem startup/prime e não devem ser
subtraídas dos totais das janelas móveis. O restante do core não foi separado
entre tempo de CPU e espera do escalonador; não declarar saturação da CPU.

## Comparações que não resolveram

Patch0014 habilitou somente no diagnóstico de conteúdo limitado a temporização
por software já existente no muOS, desligando a espera vertical solicitada.
Parser, restrições de conteúdo e encerramento permaneceram iguais. Host
pacing-host.5v5cxz55 passou loader/CLI noQEMU. No aparelho swap_interval0 e
vsync_effective0 foram confirmados, mas a apresentação continuou em5,376ms,
o core em13,415ms e o limite em52,47fps. **Não promover esta variante.**

`build-phase4-nes-optimized.py` recompilou o MESMO arquivo fonte fixadoFCEUmm
ac0d00a7fc01166f84c7bac01d1084ebfd2b865e, com include de Makefile posterior
ao upstream: O3/LTO/fno-semantic-interposition, preservando PIC/defines/ABI A35,
RELRO/NOW, sem fast-math. Não modificou fonte do core, SDK nem ROM. Stage
core.uu8rr3el, ELF SHA9300239f0397c60a317a332edc79ff9e3ab288e58437232ff5fcd0ec4d7bf08b.
APIQEMU real passou160frames, pixels3cores/38nave/160estrelas, entrada4direções,
reset/serialização e127782frames de áudio digitalzero, iguais ao baseline.
O compilador sinalizou uma leitura em transformer.c, mapper não exercitado por
este NROM; não generalizar a validação a outros mappers ou jogos.

No console, core12,673ms e apresentação5,678ms:53,57fps com640faltas de áudio.
É um ganho limitado, **não uma correção de velocidade**. Esta compilação também
permanece experimental; C47 `nes-core/latest`, host, core e provas anteriores
continuam preservados. Não instalar nenhum dos candidatos.

## Guardas e observação física

`check-phase4-nes-profile.py` passou11fixtures descartáveis, incluindo escolha
automática/física, marcador com valor/modo/link inválido, erro do app, CSV
ausente/symlink/grande e execução duplicada. Elas não executam core real.
O modo observe preparado reutiliza o selectC47/C46 e exige perfil anterior do
mesmo boot/core/ROM/host com pelo menos59fps; **não foi executado fisicamente**.
A tentativa com o candidato53,57 foi recusada localmente antes de alocar ou
contactar o console. A disponibilidade do usuário não foi convertida em nova
aprovação visual/acústica; o áudio desta ROM continua silêncio digital.

## Game Boy preparado

[Gambatte Libretro](https://github.com/libretro/gambatte-libretro), commit
77f2567d718b8973d02caa2daa8dce4953faf811, foi fixado por ls-remote e seu COPYING
GPLv2 foi lido antes do build. Arquivo fonte retido em cache/build, SHA
45e63bc79390093b78de025172ea289ded139f4ecf1e8072242f34d7dd540338.
`build-phase4-gb-core.py`: SDK containerizado, C/C++ AArch64/A35/O2/PIC,
VIDEO_RGB565=1/HAVE_NETWORK=0, RELRO/NOW, baselineSDK preservado. Stage
gb-core/build.lgsx_3c2, ELF SHA
3e0940dacb9cbcdde1b55ebc0e1d275b1dc8b034bba0e235bc56b46651200a57.

`phase4-gb-identity-check.c` carregou o ELF com RTLD_NOW noQEMU, verificou
API1/nome/extensões/conteúdo em memória e descarregou. **Não chamou retro_init
nem carregou ROM; não comprova emulação ou compatibilidade nativa.**
A cópia privada de Super Mario Land fornecida pelo usuário permanece em
port/roms/gb,65536bytes, ignorada peloGit e fora de dist/imagens. Não foi
aberta, copiada ao console ou executada nesta rodada.

## Próximo incremento

C49: API de conteúdo Game Boy e sessão RAM/RO com a ROM privada, medindo taxa
real e áudio não silencioso antes da observação de imagem/input/retorno. Não
publicar ROM ou suas capturas; usar assets e manifesto privados. A emulação NES
continua pendente de velocidade: separar tempo de CPU/espera e apresentação
antes de outra otimização. Não repetir USB, calibração, reboots, A/B ou rollback
aprovados sem relação concreta com a mudança seguinte.
