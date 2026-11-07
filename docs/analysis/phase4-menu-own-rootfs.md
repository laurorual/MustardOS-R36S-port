# Fase 4 — primeiro menu com userspace próprio

Continuação de 25/10/2026 no R35S/R36S-V12 Panel 0. **Resultado:** muxlaunch
recompilado para o SDK Buildroot executou com tela, navegação, A/B/Fn e áudio
via PipeWire, confirmados pelo usuário. Houve uma falha de restauração do
volume após o ensaio sonoro; foi detectada, reparada e coberta por uma
regressão automática. **Não houve boot da imagem, integração do init completo
ou aprovação de redistribuição do Mali r13p0.**

## Escolha do incremento

A licença do ZIP Hardkernel exato continua sem termos anexados; a pesquisa
adicional não encontrou associação suficiente para fechar redistribuição.
Em vez de declarar um provider final, este incremento compila código e
dependências abertos, mantendo o mesmo uso privado do r13p0 já ensaiado.
A [pendência do provider](phase4-r13-runtime.md) permanece explícita.

O [fragmento aditivo](../../port/device/rk-r35s-p0/phase4-menu.fragment) amplia
o SDK gráfico existente: SDL_image 2.8.12, SDL_mixer 2.6.3, SDL_ttf 2.24.0,
HarfBuzz/FreeType, PNG, curl/OpenSSL, libarchive e FFmpeg 6.1.5. FFmpeg ficou
sem CLI e com codecs/demuxers/protocolo limitados para o diagnóstico; não
houve teste de vídeo, BGM, MIDI, rede ou catálogo de emuladores.

O controlador conferiu a preservação das opções anteriores, da toolchain,
dos headers 4.4 e das revisões core/patches. Downloads passaram pelos hashes
das receitas; build ocorreu offline no container fixado, com oito jobs e
limite 12 GiB. Não foram instaladas dependências no Bazzite ou no console.
A saída mutável continua `build/phase4/graphics-config/output`, agora sob
o perfil `menu/active`. Os controladores gráficos antigos recusam alterá-la;
o teste desse bloqueio preservou o hash da imagem. Os artefatos históricos
em `dist/phase4/` continuam separados dessa saída.

## Fontes, ABI e staging

Frontend `5e8635b3…`/GPLv3 e recursos internal `550cc58f…` foram exportados
para `build/phase4/menu`, com hash por blob e avisos GPL/MIT/OFL. O
[preparador](../../port/scripts/prepare-phase4-menu.py) usa o catálogo/cache
de recursos da Fase 3, sem reutilizar seus binários Debian. Mojibake 0.3.6/MIT
foi recompilado; LVGL e demais fontes usados pelo menu também.

O [makefile](../../port/packaging/phase4-menu.mk) usa GCC 13.4, Cortex-A35 e
somente pkg-config/sysroot Buildroot. O [harness](../../port/diagnostics/phase4-menu.c)
envolve muxlaunch nativo, limita a execução a 90 s e intercepta `run_exec`
e `load_mux`: selecionar Informações encerra o ensaio, sem disparar outro
módulo, script, reset ou fluxo de boot. Não representa o frontend completo.

ELF/carregamento QEMU Cortex-A35 com `LD_BIND_NOW=1` passaram. A imagem base
de dependências tem 274 ELF AArch64, ext4/fsck aprovados e SHA256
`662a4857ccbe14c44c068c3939f91823d8823d949304e01003b12a908abc2cd8`.
O binário do menu tem SHA256
`32bc885e7ab01b871166f257701b800366223f38b96d8eabd1f2200f8baf1cf5`.

Essa imagem base ainda contém o provider antigo UK 10.6 como SDK de link;
**não foi usada diretamente para apresentar gráficos no aparelho**. O
[staging](../../port/scripts/prepare-phase4-menu-session.sh) extrai a imagem
real por debugfs/fakeroot, acrescenta menu/recursos e aplica explicitamente
o r13p0 privado, com hashes separados. Não gera uma imagem ext4 integrada
com r13p0 nem altera o SDK ou a instalação dArkOSen.

O [runner](../../port/scripts/run-phase4-menu-session.sh) prepara tudo em
`/tmp` tmpfs e usa namespaces privados. Loader, libc, SDL, codecs, fontes e
PipeWire são do userspace próprio. O supervisor Python, kernel e coldplug
continuam sendo os do dArkOSen. Não há bind de `/usr`/`lib` Debian, ROMs,
home do usuário ou boot no chroot. Só os nós necessários de input/GPU/ALSA
são expostos conforme o modo; framebuffer e Power não são expostos.

## Ensaios e resultados

| Etapa | Evidência observada |
| --- | --- |
| Inspeção sem GUI | uinput criado; SDL 2.30.12 identificou `muOS-Keys`, 15 botões/4 eixos/1 hat; controle removido e grab liberado |
| Mapping | GUID real `06004ca66d750000043500006f730000`; índices BTN medidos via joydev, KEY_VOLUME no final; valor escrito e relido do varstore |
| Menu sem áudio | EGL/readback passou antes de abrir; menu KMSDRM/opengles2 640×480; usuário confirmou texto em português, orientação, navegação, A/B/Fn e saída por Informações |
| Menu sonoro | SDL `pipewire`, 12 sons carregados, F32 estéreo/44100 Hz; usuário confirmou sons audíveis à distância normal e confirmação de A completa |
| PCM durante menu | MMAP_INTERLEAVED, S32_LE, 2 canais/44100 Hz, período 512/buffer 2048; Playback amostrado 153,153, route SPK |
| Encerramento sonoro | seleção `info`, mixer drenado em 423 ms, zero canais restantes e 150 ms de cauda; exit 0 |
| Recursos | max RSS ~57,5 MiB sem áudio e ~68,8 MiB com áudio; medições curtas, sem conclusão de estabilidade prolongada |

Para o som, o usuário confirmou um áudio conhecido antes do ensaio e ajustou
o nível: o snapshot inicial sonoro era **153,153**, diferente dos 95,95 da
inspeção inicial. O ganho de software do PipeWire ficou em unity somente na
sessão privada; o default do perfil continua 35%. Os WAVs `info_open` e
`info_close` foram trocados por `confirm.wav` **apenas no chroot de áudio**,
com hashes registrados. Os recursos originais e o problema de audibilidade
dos WAVs originais de ajuda não foram corrigidos por esse controle.

Volume/brilho físicos não foram validados: o harness intercepta pedidos de
scripts e o ensaio verificou eventos/UI. O log contém uma chamada de brilho
bloqueada. Não inferir o funcionamento completo dos controles do sistema
pela aparição de uma barra. Power, demais ombros/sticks no menu e fluxos de
suspensão/desligamento continuam fora deste recorte; uinput amplo foi testado
[separadamente](phase4-native-input.md).

## Falha de restauração detectada e corrigida

Após a sessão de áudio, o worker terminou com exit 0 e os serviços voltaram,
mas a comparação estrita do coletor falhou: Playback inicial 153,153 versus
95,95 no primeiro snapshot final. A restauração antiga aplicava ALSA **antes**
de iniciar os serviços e não verificava o estado depois. A origem exata da
escrita de 95 não foi isolada entre route/codec e componentes da subida do
launcher; atribuí-la definitivamente a um processo seria hipótese.

O snapshot inicial foi reaplicado e conferido duas vezes; a evidência da
falha foi mantida como `mixer-after-initial-restore.state`, além do estado
reparado. O [supervisor](../../port/scripts/phase4-core-session.py) agora
aguarda a subida dos serviços, reaplica o snapshot e exige duas leituras
iguais separadas por 500 ms, com tentativas limitadas. Só então anuncia a
restauração verificada.

Uma nova inspeção automática exercitou parar/subir os mesmos serviços com
o nível inicial 153,153. Passou com o snapshot final exatamente igual,
sem repetir interação gráfica/sonora. Não foi injetada perda de SSH para
validar o timer independente. Após todas as sessões: serviços ativos,
taint 0, cinco contadores Btrfs zero e Image instalado inalterado; os
temporários remotos foram removidos após a coleta.

## Retomada e limites

```sh
bash port/scripts/build-phase4-menu-deps.sh status
# configure foi executado uma vez; o marcador menu/active protege a saída.
# Para repetir um build, sem outro job ativo:
bash port/scripts/build-phase4-menu-deps.sh fetch
bash port/scripts/build-phase4-menu-deps.sh build
# Esperar build.exit=0 e container parado.
bash port/scripts/compile-phase4-menu.sh
bash port/scripts/collect-phase4-menu-legal-info.sh
bash port/scripts/prepare-phase4-menu-session.sh
```

Evidências completas ficam em `build/phase4/menu/`; os pointers `latest-*`
identificam os fixtures exatos. `dist/phase4/menu-native/` contém programa,
fontes/patches, recursos, licenças das dependências e provas, **sem** ZIP,
driver Mali, rootfs ou staging privado. A falta do arquivo fonte Buildroot
anunciada no warning legal-info é suprida por um git archive da revisão;
fontes/avisos do pacote local e do menu acompanham os artefatos.

O próximo incremento precisa fechar o provider SDK/target e seus termos,
integrar init/storage e serviços de volume/energia, e só depois preparar
boot independente. O menu e o áudio agora foram ensaiados no userspace
próprio; isso não aprova o kernel candidato ou elimina as pendências de
licença, bootloader/DDR/firmware, estabilidade e layout de mídia.
