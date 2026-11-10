# C47 — primeiro core real: integração funcional aprovada

Em01/11/2026, no boot67/C07 do R35S, FCEUmm executou uma ROM NES original,
selecionada com A pelo menu nativo. O usuário confirmou navegação da nave,
cenário corrigido e retorno ao launcher: “Tudo parece ok.”. Sessão terminou
normalmente, operação0/cleanup0, raizRO/fundação97/rede preservadas, RAM removida
e página finalC47 enviada. **Velocidade e áudio de jogo não estão qualificados:**
1544frames/30s (≈51,47frames/s) e767faltas no ring de áudio na sessão final.

## Fontes e conteúdo

[FCEUmm upstream](https://github.com/libretro/libretro-fceumm/tree/ac0d00a7fc01166f84c7bac01d1084ebfd2b865e),
commit ac0d00a7fc01166f84c7bac01d1084ebfd2b865e. README e
[Copying/GPLv2](https://github.com/libretro/libretro-fceumm/blob/ac0d00a7fc01166f84c7bac01d1084ebfd2b865e/Copying)
conferidos antes do build. Preservados avisos, Authors e arquivo completo de
fontes em build/phase4/nes-core/cache. Tarball SHA
364affeeea3d91ab8de4ef2a333cb0ca4d7d8e8992e94366a270b32e309485ca.
Nenhuma alteração em refs/; provas públicas não contêm ELF do core/GPU blob.

Conteúdo original MIT em port/diagnostics/phase4-nes-demo.py: NROM-128/mapper0,
PRG16KiB/CHR8KiB, código6502 e arte próprios, nave amarela e estrelas em céu azul.
D-pad move, APU desabilitado. Sem ROM comercial, fonte, música ou BIOS externa.
Assinatura47C3 na RAM NES e variáveis de posição permitem verificar execução
real do programa e resposta do controle, separadamente dos callbacks do frontend.

Core build.uxtwbp1g: SDK AArch64/Cortex-A35, PIC/RELRO/NOW, RGB565, HDpacks e
filtroNTSC desabilitados, sem flags ARM32/x86. SDKbaseline preservada. ELF SHA
53b233ded89c32f847d137ed990bc581b6a1e7efe20481b74bd7da73ada9adad.
A revisão final só da ROM é rom.qs99107a, SHA
595157b8ab6b9188d60f4ffb8a909cd80c8807a3873ffeabae7f59df3abe5eca.

## Host, guardas e ciclo de vida

Patch0012 adiciona --diagnostic-content ao host privado C44. Requer arquivo,
prazo1..60s e fresh; recusa no-content, restart, netplay, subsystem e single-screen
nessa modalidade. Sem opt-in, regras anteriores preservadas. Carga real de
conteúdo segue o loader normal; diagnóstico não inicializa achievements/netplay.
Primeiro-present, prazo e saída normal/cleanupSDL permanecem C44. Host final
host._t02eefb, SHA2ba1ca32d2e3c7c9157d07043ecab26a8ef0913871dca0400fe57b66b92d7bc1.
C44 aprovado não foi modificado ou instalado novamente.

UI/adapter/worker/supervisor C46 são reutilizados e conferidos contra as provas
imutáveis. App único escolhido por A; opções governor/controller consumidas sem
aplicação em CPU. Launcher C47 valida dois assets fixos por hash/tipo/modo/link,
exige /mnt/mmc emtmpfs, recusa symlinks/arquivo preexistente e copia só a ROM
própria para ROMS/NES, modo400. Executa core+arquivo com fresh/diagnostic-content/
30s; não aceita comando ou caminho arbitrário vindo do pedido.

Namespace /run/muos e /tmp, dadosRO+noload+RAMprefs, configRAM, sysfsCPU/powerRO,
core30s/retorno20s/seleção120s e página final são mantidos. Sem saveback, reboot,
tokenC12/C25, instalação, kernel/DTB/partição ou recomposição da imagemC38.
Original32 intacto, SteamDeck fora do fluxo.

## Verificação

| Prova | Resultado |
| --- | --- |
| Core/API real em QEMU | api._zynd251:160frames, RGB565/256x240, RAM/CPU/input4direções/reset/serialize/unserialize/unload |
| Pixels reais do core | 3cores;38pixels da nave e160de estrelas, sem cópias extras |
| Áudio em checker |127782frames,48000Hz,max_abs0; ROM silenciosa |
| Host/launcher | checks.9ueiqiq3:40parser/8guardas, loaderCLI/LD_BIND_NOW |
| CPU real R35S semUI | cycle.i1vk3010: mesmo API/pixels mais6guardas, operação0/cleanup0 |
| Seleção física final | observe.cpvhbmpp: A/nave/D-pad/cenário/retorno aprovados, core1544frames/30s, operação0/cleanup0 |

Header e API foram testados com o loader C38. O checker simula entradas e lê a
RAM emulada para confirmar CPU/PPU e restauração, sem inicializar SDL/GPU/ALSA
ou entrada física. Essa prova antecedeu a gráfica. Os40casos do parser incluem
18legados/11prazo/11conteúdo. Oito guardas recusam ROM alterada/ausente/symlink,
manifest estranho, FS persistente, arquivo preexistente e caminhoROMS symlink.

Perguntas físicas ocorreram após recibos de apresentação e PID/starttime ativo.
Coletas compararam bytes das preferências e mounts globais, mixer/DRM/caches,
rootRO/97/taint0/infraPIDs/rede. Tudo restaurado; MUOSDATA desmontado e cápsulas
removidas. Console seguro67/IP192.168.15.16:2222, PCMclosed, sem UI/core ativo.

Prova funcional dist/phase4/nes-core-content, com checksums, fonte própria e ROM
original MIT, receitas e relatórios. Sem ELF/core/imagem/blob/prefs reais/segredos.
Prova adicional dist/phase4/nes-core-performance-observation preserva o achado
adverso de throughput/ring, sem alterar a prova funcional já congelada.

## Correção da ROM e limite de desempenho

A primeira observe.5ax7pcci aprovou abertura/input/retorno, mas o usuário notou
cópias azul-claras da nave no cenário. Era erro do nosso gerador: AND7 deixava
índices1..7 nos espaços do nametable, incluindo tile1 da nave. Agora grava tile0
nos espaços e tile2 nas estrelas. O core emulava o programa corretamente.
Revisão ROM-only preservou os ELFs de FCEUmm e muxretro. Novo teste quantitativo
de pixels noQEMU/CPU e observação final confirmaram o cenário. Parser/launcher/
UI/supervisor aprovados não foram recompilados ou repetidos por essa mudança.

Na sessão final, metadados reportam nominal60,099827Hz/locked59,94, mas o
contador de execução registra1544frames no prazo30s. Isso não qualifica velocidade
integral. O log também registra767faltas no ring e correção de taxa+0,5%.
A causa ainda não foi isolada; não atribuir ao core, CPU ou driver só por esses
números. Próximo diagnóstico deve separar tempo em core/render/espera/áudio e
negociação48000/44100 antes de alterar clocks ou repetir calibração/IRQ/prime.
ROMsilenciosa não qualifica música, efeitos ou acústica de emulador. Serialização
foi testada em memória; saves persistentes e longa duração não foram testados.

## Próxima entrada de teste fornecida pelo usuário

Durante a última rodada, usuário disponibilizou sua cópia de GameBoy em
port/roms/gb/Super Mario Land (World) (Rev 1).gb. Arquivo65536bytes presente e
preservado. /port/roms/ foi incluído em .gitignore; não está em dist ou imagens.
Autorização é uso privado em teste com core GameBoy apropriado. Preferir esse
conteúdo quando aplicável, sem gerar nova ROM. Ainda não foi emulado ou copiado
para o console; não confundir com o coreNES já validado.

C48: investigar throughput/buffers do caminho de conteúdo; preparar coreGameBoy
com fontes/licenças/ABI fixados para a ROM privada, mantendo snapshots/manifest
privados fora de qualquer publicação. Não trocar kernel/DTB/boot ou recalibrar
volume sem evidência concreta. Nenhum novo ensaio está armado.
