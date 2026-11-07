# C41–C43 — muxretro nativo, carga sem conteúdo e isolamento em RAM

## C41: compilação e contrato do host

A revisão é a mesma do frontend já aprovado:
`5e8635b3b485eec9ad2ace141c415fd2df47d8f1`, archiveSHA
`c638d1afd4d995792f5ee09ea647de6976a60ca80e82014591a3fdff400ee5ff`.
Foi extraída para uma cópia privada; refs/ e as libs aprovadas não foram alterados.
O host mantém a implementação nativa de renderização, áudio, input e core.

Rcheevos é a dependência nova, MIT, fixada pelo script upstream do snapshot:
commit `2ad0b8672f68a48148620164510b963039e49eb1`, archiveSHA
`b8e3e834d15c327085154315c49dea85b081ad48592ba1740f323ac953e1bfec`.
Fonte pública: https://github.com/RetroAchievements/rcheevos/tree/2ad0b8672f68a48148620164510b963039e49eb1 .
Hash e licença foram conferidos antes de compilar. Excluídas as integrações
externa/DLL como no script upstream. Libarchive/OpenSSL/GLES/zlib vêm do SDK.

Patch0007: `muxretro core.so --no-content` exige anúncio positivo de suporte,
chama `retro_load_game(NULL)` e não faz precache/hash/achievements/netplay de
um arquivo inexistente. A identidade lógica usada para configurações não é
passada ao core como conteúdo; o diretório relativo fica vazio nesse modo.
O restart preserva o argumento. Caminho normal de ROM permanece separado.
Modo sem conteúdo é fresh e recusa netplay/subsystem/single-screen.

Patch0008 inclui stdint antes do DRM do SDK. O builder ainda fornece aliases
privados libarchive/ para headers planos e flags-MMD/-MP/-lz explícitos.
As tentativas host a9g2mopo/zxxwgn4a/0059dj5q/7wnhyvm_ estão preservadas; falharam
antes do ELF final e não fizeram implantação. Há avisos de truncamento em código
upstream e avisos dynsym do fornecedorEGL; não foram alterados blobs para ocultá-los.

Build final: `build/phase4/muxretro/build.h6bh_1rk`,
SHA256 `a5aa04c95374bef318317e9aeb47a397700fda82799b9a27ad0adbf87b887c4e`.
AArch64/Cortex-A35/PIE/RELRO/NOW, RUNPATH/opt/muos/frontend/lib. As bibliotecas
C38 e SDKconfig permaneceram intactos. Não é rebuild de firmware.

18casos do parser real e loader real extraído+coreC40 passaram noQEMU:
`no-content-checks.4_6c9frt`. Recusas incluem falta de anúncio, opt-out, callback
nulo e core rejeitando carga. A carga positiva valida NULL, estado e um frame.
As seis fontes de parser/loader/main testadas coincidem com o build final.
`audit.l8821jme` conferiu ELF completo, dependências/LD_BIND_NOW, --version,
--help e recusas antecipadas. Não executou inicialização gráfica.
Prova `dist/phase4/muxretro-host-preparation`, sem ELF ou blobs.

## C42: verificação automática na CPU do R35S

Usuário ausente autorizou trabalho/testes autônomos; nenhuma ação por botões.
No boot65, trêsELFs foram conferidos e enviados apenas àRAM: muxretro,
checkerC40 e coreC40. Cada comando recebeu prazo10s pelo helper instalado.
Version/help/recusa de argumentos e checker11frames/8085frames áudiozero passaram
naCPU real, com binding imediato. Isso qualifica CPU/loader/API, não vídeo,
PCM, display ou input físico. Não houve sessãoSDL ou reboot.

Primeira tentativa cpu.5gwc38vx parou antes dos binários: diretório de trava
inexistente noC07. Cleanup passou; corrigido com criaçãoRAM700 e recusa de
symlink/modo/dono/lockocupado.6fixtures usando flock real passaram.
Sucesso: `muxretro/cpu.dnoxrsg9`,3ELFs removidos; rootRO/97/rede/PIDs/PCMclosed
preservados. Prova `dist/phase4/muxretro-native-cpu`.

## C43: isolamento de dados ensaiado no aparelho

`muxretro/storage.cuxdp3yn`: namespace privado sob a trava de sessão, usando os
guardsC22 existentes. MUOSDATA real montado RO+noload/nosuid/nodev/noexec;
somente MUOS/preferences foi copiado paraRAM e carregado (55/70). Nenhum registro
persistente foi inicializado ou salvo. Hashes originais antes/depois idênticos;
não estão nas provas públicas. Não foi necessário leitor/SteamDeck.

Config de storage foi sobreposta SOMENTE no namespace para fstypetmpfs,
com userdata emRAM. O S90 original criou e validou os aliases, e escrita
canônica em storage/pickles foi vista apenas nas duas referênciasRAM, ausente
no volume real. S90stop e desmontagens em ordem passaram; /proc/1/mountinfo
ficou byte-idêntico e todas as cópias/arquivos foram removidos. RootRO/97/rede/
PIDs preservados, sem gráfica/áudio/input.10fixtures de guardas/cleanup passaram.
Prova `dist/phase4/retro-ram-storage`. Todas as três provas têm SHA256SUMS conferidos.

## C44: sessão gráfica e direcional concluídos

O worker isolado, supervisor de descendentes, proteção sysfs e saída normal
por prazo foram implementados e qualificados no boot65. Houve 2700frames/45s,
confirmação física do direcional com processo ativo e limpeza/restauração0.
Ver [C44 e próximo incremento de despacho/retorno](phase4-retro-session.md).
O core gera áudiozero; não houve aprovação acústica de jogo ou instalação
persistente. As provas históricas C41–C43 acima permanecem imutáveis.
