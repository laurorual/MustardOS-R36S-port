# Fase 4 — C06: frontend com áudio no kernel próprio

**Estado atual: revisão4/BOOT0017 aprovada; coleta e saúde concluídas.**
Menu/submenus e áudio foram confirmados com navegação adaptada +8,8dB,
confirmação/back originais e ajuda com confirmação de controle. Prova em
`dist/phase4/native-frontend-audio-boot/`; conclusão ao fim deste documento.
As seções de revisões anteriores abaixo registram a investigação histórica.
Alvo exclusivo:
R35S genuíno, RK3326, R36S-V12/Panel0, kernel4.4.189-muos-r35s-p4. Junta o
frontend supervisionado [C04](phase4-native-frontend.md) ao áudio audível
[C05](phase4-native-audio.md), inicialmente sem hotkeys/rede/conteúdo/Power.

O blueprint inicial foi `build/phase4/linux-diagnostic/frontend-audio.t5f0ynhq`,
ponteiro `latest-native-frontend-audio`; não contém seed. Apenas bootstrap,
runner, helperC06 e marcador foram instalados, com preimages e guarda de
identidade do cartão secundário. Kernel/DTB/U-Boot/tabela/bibliotecas e
binários permanecem os mesmos já exercitados, não importados de outro rootfs.

## Escolha e evidência

S95/S80 iniciam PipeWire/WirePlumber após entropia, udev/D-Bus e storage.
S99 inicia o supervisor como pai real do frontend, espera first_paint novo
e seleciona SDL_AUDIODRIVER=pipewire se core/audio existe
([serviço](../../port/device/rk-r35s-p0/S99muos-ui)). Frontend e supervisor
foram auditados por ELF/loader/QEMU no sysroot próprio desta imagem. Isso
não substitui execução conjunta e confirmação física no novo boot.

O [helper](../../port/device/rk-r35s-p0/frontend-audio-diagnostic/session.sh)
prepara **antes do cache S95** cópias voláteis dos diretórios globais/device
de configuração e do perfil ALSA. RotaSPK_HP, Playback157, software100%,
som2 e idle0 mantêm o recorte audível C05, com opções coerentes para a UI.
Diretórios são bind-mounted a partir de /run porque `muvarctl` usa rename
atômico em `refs/muos/frontend/common/config/var_store.c:315–360`; bind de
arquivo individual impediria esse fluxo. Originais ficam protegidos.
São copiados apenas diretórios de configuração do candidato para /run,
não a raiz viva; nunca /var/lib/muos-seedrng ou material de seed.

Ajuda usa temporariamente `confirm.wav` sobre info_open/info_close por bind.
Esses recursos originais já ficaram baixos/inaudíveis nos ensaios anteriores;
o objetivo é validar o caminho de eventos, não aprovar os WAVs originais.
Hashes dos originais são comparados após desmontar. Navegação/confirm/back
mantêm os recursos do tema. `audio.c:204–228` carrega o diretório de som do
tema para snd_type2, enquanto S99 evita hotkeys neste ensaio.

## Ensaio limitado e encerramento

Janela de90s após prontidão; pedir navegação por menu, Informações,
Configurações, ajuda Fn/B e retorno ao menu. A/B navegam normalmente;
Informações não encerra o teste. Não usar Power/volume/brilho nem alterar
configurações. Soltar controles ao terminar e aguardar diagnóstico.
Há margem de3s antes do stop: não é medição instrumental de drain SDL/
PipeWire nem garantia sobre um novo toque no instante final.

Registra pai/first_paint, SDL_AUDIODRIVER do processo, módulos observados,
modo DRM antes/depois, grafo e PCM/rota/ganho/software após a prontidão e
antes da parada. Requer ambos os snapshots de áudio válidos, sink esperado
e ACPfalse. A audição e a integridade do último efeito dependem também do
relato do usuário; status0 não estabelece audibilidade.

Stop nativo S99/supervisor antecede a parada do core. Cleanup tenta UI mesmo
após falha parcial; remove binds de ajuda/UI/config/perfil/core, restaura
ALSA pré-core e cache a partir dos arquivos originais. Confere dez hashes
de perfil/opções/ajuda antes/depois. Logger nativo para via SIGTERM depois
dos últimos clientes, como C05; raiz retorna read-only. Falhas preservam
DIAG08/BOOTnnnn, com status de reprovação e FAT desmontada.

## Verificação e limites atuais

Nove fixtures executam os hooks reais com caminhos relocados e binds
simulados: sucesso, falha em cada uma das sete montagens e falha de stop
do áudio. Simulam gravação atômica dentro dos diretórios temporários e
conferem restauração de todos os originais/cache. Não montam dispositivos
ou acessam áudio/seed reais. Auditoria shell em BusyBox AArch64/QEMU,
loader e e2fsck do blueprint passaram. Ainda não é validação física C06.

Depois do boot, retornar ao dArkOSen e coletar DIAG08 read-only em namespace
privado, preservando as montagens globais. Verificar input/entropia/parada,
root ro, fsck offline e saúde do original antes da aprovação. Calibração de
volume final, ajuda original, fones, hotkeys, shutdown, rcS completo, rede,
conteúdo e outros painéis continuam fora do recorte.

Prova pré-boot: `dist/phase4/native-frontend-audio-preboot/`. Instalação de
quatro arquivos com releitura/fsck e saúde stock aprovada; p2 desmontado e
temporário removido. Nenhuma aprovação física C06 até a coleta posterior.

Primeiro retorno físico: `muOS C06: STOPPED / Services check failed; DIAG08
saved, root ro`. Não atribuir causa antes da coleta. Usuário orientado a
retornar ao original e preservar a tentativa, sem repetir o boot.

## Falha r0 identificada e correção r1

DIAG08/BOOT0013, `frontend-audio.t5f0ynhq/boot1`: status1, usuário não viu
menu. Core/input subiram, S80 registrou `Audio finalised (node=35, volume=35%)`;
helper rejeitou a pré-condição de100 antes de chamar S99. Nenhuma prova de
frontend sonoro. Nove hashes originais, ALSA pré-core/cache/binds/parada/
logger/rootro/fsck/saúde passaram. A prova negativa foi congelada em
`dist/phase4/native-frontend-audio-boot-policy-failure/`.

A preparação inicial não considerou `settings/advanced/volume=2`:
`refs/muos/internal/script/var/audio.sh:96–106` retorna35 fixo nesse modo,
independentemente do salvo100. `S80pipewire.sh:375–381` reaplica o valor.
Isso é conflito da preparação diagnóstica com política nativa; não há
falha de tela ou do frontend demonstrada nessa tentativa.

Revisão1 escreve política3 somente na cópia /run: usa software máximo do
board100/unity (ganho hardware continua157) e evita LOAD_SINK_VOLUME do
ramo de outras políticas em `S80pipewire.sh:420–428`. Avaliação literal da
função nativa, sem modificação de refs ou cópia para código do port, confirmou
2→35 e3→100 com salvo100. Emite path/volume/política antes das condições.
O décimo hash e a reconstrução do cache incluem a política original2.

Nove fixtures de cleanup foram repetidas com o campo adicional, além das
duas avaliações de política. Auditoria QEMU/shell/fsck passou; apenas
`usr/libexec/muos-c06-session` atualizado no cartão, com preimage e hashes
de bootstrap/runner exigidos. Rootfs host sem seed em
`frontend-audio-policy.hwhmotll`, `latest-frontend-audio-policy`, próxima
coleta `boot2`. Prova `dist/phase4/native-frontend-audio-policy-preboot/`.
Temporário removido, p2 desmontado e stock saudável antes do novo poweroff.
Ainda falta a validação física conjunta de UI/áudio.

## Revisão1: PCM válido, áudio ainda reprovado

BOOT0014/status0, `frontend-audio-policy.hwhmotll/boot2`: menu apareceu;
usuário relatou áudio baixo, apenas barulho ao entrar/sair, D-pad inaudível.
Não aprovar C06 pelo status0. First_paint/S99/pai, DRM, ALSA/config/cache/
binds/parada/logger/rootro/fsck/stock passaram. Módulos observados incluem
muxinfo/muxplore/muxcollect, mas não muxconfig; este submenu não foi aprovado.

Duas amostras mostram S32_LE/stereo44100, Playback157/SPK_HP, software1,00.
StreamSDL é F32LE/stereo44100 e seus volumes também1,00. C05 audível usou
48000. O hash do navigate.wav coincide com o staging usado nos ensaios
anteriores; não há troca de recurso demonstrada. RMS do arquivo inteiro
navigate223 versus tomC05 2509 é diferença digital, não prova de loudness
ou causalidade no hardware. Originais e confirmação do usuário preservados
em `dist/phase4/native-frontend-audio-quiet-failure/`.

Próxima comparação proposta: tom48k antes da UI, tom44100 com UI ativa e
um tom curto controlado nos eventos. Manter ganho/rota/software constantes.
Não trocar driver, compilar frontend ou elevar ganho sem evidência adicional.
Esta revisão comparativa ainda está em preparação no host.

## Revisão2 comparativa instalada, ainda sem teste físico

Host sem seed `frontend-audio-compare.ln84xpst`, `latest-frontend-audio-comparison`.
Prova `dist/phase4/native-frontend-audio-comparison-preboot/`. Mantém ganho157,
SPK_HP e softwareunity. A reproduz WAVC05/48k antes da UI; B reproduz três
vezes o tom curto44100 com UI aberta, exigindo hw_params de cada taxa durante
as reproduções. Depois confirm/back/navigate/info_open/info_close usam esse
tom por binds em /run. Originais protegidos e13 hashes comparados ao fim.

Tom: primeiros250ms do C05, resample linear48000→44100 e fades adicionais
5ms, sem amplificação, canais idênticos. Pico6548 e RMS4556, abaixo do pico
6553 original. Arquivo PCM16/stereo44100,11025frames/0,25s,44144bytes.
Hash `a911622806004cbc123efe2ba4129ebfa1af2fcd9b8b4da2a75a40e114ed3d14`.
Doze fixtures cobrem até dez binds e stop falhando. Shell/QEMU/ext4/fsck e
instalação de dois scripts/um WAV passaram; kernel/DTB/U-Boot/libs intactos.
Stock saudável, candidato desmontado, temporário removido antes do poweroff.

Separar audição de A, B e efeitos. Um controle audível ainda deixa a
qualidade/adequação dos recursos originais pendente; comparar taxas exige
os snapshots reais, não apenas o sample rate do arquivo. Nenhuma causa
entre driver/rate/SDL/recursos foi afirmada antes desse ensaio.

## Revisão2: controles ouvidos nas duas taxas, nível ainda baixo

BOOT0015, `frontend-audio-compare.ln84xpst/boot3`: usuário ouviu seis bipes
A/B e os mesmos bipes em D-pad/A/B/Fn. Volume baixo/audível, estimado
subjetivamente em40% do dArkOSen. Logs confirmam48k noA,44,1k noB/UI,
S32/stereo,157/SPK_HP/unity; muxtypesinfo/config/explore observados.
As treze hashes, ALSA/cache/binds/logger/rootro, regressão entropia/input,
fsck offline e saúde stock passaram. Prova imutável
`dist/phase4/native-frontend-audio-control-comparison/`.

A análise aprova apenas comparação controlada. Não comprova qualidade dos
originais nem identifica sozinha a causa da diferença: além de trocar WAVs,
r2 teve reprodução antes da navegação. R3 em preparação restaurará somente
navigate/confirm/back originais, preservando sequência A/B e nível157.
Ajuda usará confirm original como controle. Sem elevar ganho nessa rodada.

## Revisão3 instalada: efeitos originais com referências mantidas

Blueprint `frontend-native-effects.xbxgwf0j`, ponteiro `latest-frontend-native-effects`;
prova `dist/phase4/native-frontend-native-effects-preboot/`. Somente helper
atualizado: modo c06_control_effects0 deixa navigate/confirm/back originais;
ajuda usa confirm original, como r1. Referências A/B e157/SPK_HP/unity
permanecem. Treze hashes/mesmo cleanup. Vinte e uma fixtures cobrem modos
controle/nativo, falhas parciais de montagem e stop de áudio. QEMU/shell/
fsck/instalação/saúde passaram; kernel/DTB/U-Boot/libs intactos. Temporário
removido e candidato desmontado. Falta a validação física desta revisão.

## Revisão3: original de navegação ainda muito baixo

BOOT0016/status0, `frontend-native-effects.xbxgwf0j/boot4`: usuário ouviu as
referências e confirmação/back, mas navigate original somente ao ouvido.
Manteve referências/ganho/taxas; a forma dos efeitos era o fator alterado
em relação à revisão2. Muxinfo/muxconfig e outros módulos observados;
restauração de13 hashes/ALSA/cache/binds, logger/rootro/entropia/input/
fsck/stock passaram. Prova `native-frontend-original-navigation-quiet/`.

A análise digital confirmou o navigate idêntico ao blob upstream
`share/theme/MustardOS/sound/navigate.wav`, SHA7b2c53f0…540d7. PCM16,
estéreo44100,38016frames; pico10892/RMS223. Confirmação:3490frames,
pico22154/RMS2075. Comparar RMS sem levar duração em conta não equivale a
loudness por ação. Energia por evento da navegação é cerca de1/7,95 da
confirmação; um ganho linear limitado a pico30000 resulta2,754315×,
+8,80027dB, energia95,44% da confirmação e zero clipping. Forma temporal,
duração/taxa/canais serão preservados. Percepção precisa de validação humana.

R4 em preparação aplica somente esse ajuste por bind temporário sobre
navigate.wav. Sem elevar o ganho do codec, alterar confirmação/back, taxa
ou referências A/B. Licença GPLv3 do upstream verificada; recurso original,
commit, hashes e modificação serão documentados e licença retida no pacote.
A primeira geração host foi rejeitada por literal de checksum transcrito
incorretamente; corrigido antes de qualquer instalação. O dado gerado
foi reproduzido e seu conteúdo/limite de pico conferidos. Campo de tamanho
maior que128KiB no instalador é exceção exclusiva para path/152142bytes/
SHA exatos, como já havia para o WAVC05; não amplia outros assets.

## Revisão4 instalada: ganho exclusivo no arquivo de navegação

`frontend-navigation-level.ed62uz58`, `latest-frontend-navigation-level`;
prova `dist/phase4/native-frontend-navigation-level-preboot/`. PCM original
multiplicado por2,754315 (+8,800272dB), pico30000 e clipping0; preservados
38016frames,44100Hz,estéreo e todos os bytes RIFF/LIST fora do bloco PCM.
Energia por evento95,44% da confirmação; isso não determina loudness no
speaker. WAV152142bytes, SHAadac78795e6810ce5d17effa5593e9de87051d3ef36231ba9d530921951bb3ee.

Original coincide com blob do refs/muos/internal; GPLv3/root LICENSE
verificada antes da adaptação e mantida com nota/commit/hashes no pacote.
A imagem já contém a mesma licença em /usr/share/licenses/muos-core.
A exceção de tamanho do installer exige somente path/tamanho/hash exatos.
Versão intermediária de host com container WAV reemitido foi descartada;
o dado final mantém até os chunks não sonoros originais para isolar nível.

Novo modo ajusta somente navigate por bind. Confirmação/back originais,
ajuda com confirm, A/B/157/SPK_HP/unity permanecem. Trinta e uma fixtures
cobrem três modos e falhas parciais; shell/QEMU/ext4/fsck/releitura/saúde
passaram. Somente um WAV/um helper instalados; original protegido, candidato
desmontado e temporário removido. Falta audição/DIAG08/coleta desta revisão.

## Revisão4 concluída — C06 aprovado no Panel0

DIAG08/BOOT0017, coleta `frontend-navigation-level.ed62uz58/boot5`:
usuário ouviu navegação tão bem quanto os outros efeitos e confirmou
encerramento na tela esperada. Analisadores de frontend/áudio e entropia
passaram. Módulos muxlaunch/muxplore/muxinfo/muxconfig, pai S99 e first_paint
novo, SDL/PipeWire, PCM S32_LE/estéreo44100, Playback157/SPK_HP/unity.
Treze hashes originais, ALSA pré-core/cache, binds/logger/rootro, fsck e
saúde stock passaram. Prova `dist/phase4/native-frontend-audio-boot/`,
16 hashes conferidos na retomada.

A aprovação inclui navigate adaptado +8,800272dB, confirmação/back
originais e ajuda com confirmação de controle. Não aprova o WAV original
da ajuda, loudness calibrado, hotkeys/fones/energia ou estabilidade longa.
A tolerância de3s antes da parada não equivale a medir drain de áudio.
Original32 permanece recuperação; cartão candidato desmontado ao retorno.

Por solicitação do usuário, o próximo incremento passa a ser Wi-Fi/SSH
na candidata, antes de hotkeys/volume/brilho. Com8% de sessão restantes,
a preparação atual se limita ao host; sem novo boot ou escrita de mídia.
