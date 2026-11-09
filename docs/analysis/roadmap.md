# Roadmap do port nativo AArch64 muOS para R35S

Planejamento de 23/10/2026, atualizado após os ensaios de 24/10/2026, limitado ao RK3326 genuíno e ao painel `R36S-V12 2023-08-18 Panel 0`. Evidências, commits e classificação F/U/H estão na [matriz de compatibilidade](compatibility-matrix.md). A **Fase 1 foi concluída**: `muinput --list-devices` AArch64 executou com status0 ([relatório](phase1-muinput.md)). Na **Fase 2**, framebuffer e SDL/GLES passaram com confirmação visual; um perfil próprio de input executou nativamente e cobriu os controles, com ressalva de unicidade em L3 ([relatório](phase2-display-input.md)). Na **Fase 3, o recorte funcional do primeiro menu está validado com ressalvas**: tela/input, áudio de navegação/confirmação, eventos sonoros de ajuda com WAV de controle e restauração de serviços/mixer passaram ([primeira sessão](phase3-native-menu.md), [retomada de áudio](phase3-audio-resume.md)). Os sons originais da ajuda seguem inaudíveis no speaker. A [recuperação](storage-recovery.md) permitiu as novas execuções, sem recorrência dos erros anteriores nessas sessões curtas. A **Fase 4 foi iniciada**: kernel/DTB/módulos candidatos e rootfs headless compilados no host; auditoria ELF/ext4/QEMU e probe nativo da nova libc passaram ([relatório](phase4-bsp-foundation.md)). Os avanços posteriores de boot próprio estão descritos na Fase 4 abaixo; as fases 5–6 continuam sem execução.

## Abordagem escolhida

Preservar frontend, muinput e contratos de configuração/serviços do muOS. Criar um perfil R35S próprio e adaptações pequenas sob `port/`, usando dArkOSen para entender o hardware já funcional e ROCKNIX para comparar DTS, drivers e suporte de painéis. Não tomar um perfil G350/Pixel como implementação pronta.

Como ponto de partida estrutural, o G350 oferece RK3326, 640×480 e dois sticks. O Pixel 2 contribui com referências de framebuffer, sysfs e power, mas sua ausência de sticks e módulos vinculados ao kernel afastam uma cópia direta. O backend evdev portátil é preferível a ler GPIO/ADC diretamente em userspace enquanto já existe um driver de gamepad funcional (matriz E6–E7).

Separar dois sysroots: um para os ensaios temporários no Debian instalado e outro para o firmware autônomo. Um artefato só pode ser reutilizado entre eles depois de comprovar loader, símbolos, dependências, kernel mínimo e stack gráfico. Buildroot aparece nos exemplos de toolchain muOS, mas sua configuração reproduzível ainda precisa ser identificada; não há base para afirmar que bastará executar um script dos três repositórios muOS.

## Fase 0 — Fechar a linha de base sem alterar o aparelho

**Objetivo:** transformar as informações fornecidas pelo usuário em inventário verificável, antes de qualquer deploy. O usuário forneceu o primeiro levantamento; os dados necessários ao ensaio de ABI foram complementados por SSH na Fase 1. Os demais itens abaixo continuam pendentes, conforme o relatório.

Em uma sessão futura autorizada, coletar por leitura:

- `uname -a`, `getconf LONG_BIT`, `/etc/os-release`, `/proc/cmdline`, alvo de `/proc/1/exe`, DT model e compatibles em `/sys/firmware/devicetree/base/`.
- `findmnt /`, `findmnt /boot`, `lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS`; nenhum fsck, resize ou remount. Ler configurações de boot/fstab e hashes dos DTBs e kernel efetivamente usados.
- `/proc/bus/input/devices`, nomes em `/sys/class/input/`, capabilities e ranges de cada source. Não assumir event4; incluir gamepad, power e volume separados. A captura interativa futura deve usar evtest sem `--grab` e sem injetar teclas.
- `/sys/class/drm/*/status`, modos disponíveis, dados fb, backlight `brightness/max_brightness`, driver GPU e permissões dos nós. Não fazer modeset neste inventário.
- `/proc/asound/cards`, `aplay -l`, `amixer -c 0 scontrols` e leituras de mixer; unidades PipeWire/PulseAudio/ES/ogage/Fn/bateria habilitadas. Não alterar volume.
- Propriedades de `/sys/class/power_supply/*`, RTC, thermal e LEDs. Distinguir mV/µV, percentual e sinal de carregamento; não escrever em GPIO/PWM.
- Loader ELF e versões de libc/SDL/EGL/GLES/GBM/DRM, plugins ALSA, libstdc++, bibliotecas transitivas e eventual userspace 32 bits. Derivar de ELF e pacote instalado, não só de `uname -m`.

Os comandos curtos exemplificam o primeiro levantamento:

```sh
# Proposta: executar no R35S em etapa posterior, somente leitura.
uname -a
getconf LONG_BIT
cat /etc/os-release
cat /proc/cmdline
tr '\0' '\n' < /sys/firmware/devicetree/base/model
findmnt /
findmnt /boot
cat /proc/bus/input/devices
```

**Saída:** registro de hardware/ABI, DTBs/kernel identificados por hash e lista de lacunas. Isso não é backup recuperável do cartão. Antes de futuras operações de boot, planejar cópia verificável do cartão e recuperação; não criar nem gravar essa cópia nesta etapa.

**Critério para avançar:** confirmar identidade do Panel 0, rootfs/loader reais e recursos necessários ao teste pequeno. Divergência de modelo/SoC interrompe a suposição de compatibilidade e reabre a matriz.

## Fase 1 — Menor primeiro teste executável: muinput em modo de listagem

**Pergunta respondida:** conseguimos carregar e executar um componente C nativo muOS AArch64, construído para o userspace/kernel reais do R35S?

Escolher `muinput --list-devices`, compilando somente `frontend/input/`. O subprojeto não depende de SDL e liga `libm/libc` e `librt` conforme toolchain; tem Makefile próprio. `input/main.c:146–151,268–295` retorna da listagem antes da seleção de backend, criação de runtime, gamepad ou abertura de fontes. Pode ler a configuração opcional de intensidade, sem inicializar hardware. É um teste menor e mais controlado que iniciar o frontend ou o daemon (matriz E6).

### Preparação no host — executada

1. Após autorização para implementação/build, criar cópia de trabalho das fontes sob `build/`; manter código original de port/wrappers futuros em `port/`. Não compilar em `refs/`, inclusive com `make -n`: Makefiles e wrappers têm efeitos de escrita (E8).
2. Usar container rootless com ferramentas dentro do container, imagem fixada por digest, sysroot de teste Debian coerente e dependências versionadas. Não instalar dependências no Bazzite. Não incluir credenciais ou dados pessoais na cópia de sysroot.
3. Compilar só o Makefile de input, com compilador AArch64 explícito, `BUILDDIR` dentro de `build/`, flags C11/proteções adequadas ao compilador e baseline `-march=armv8-a`. Não executar `build.sh` global nem o alvo `check` do subprojeto durante cross-compilação. Guardar comandos/versões e hash do resultado.
4. Revisar ELF sem executá-lo: `file`, `readelf -h -l -d --version-info` e atributos/notas quando aplicáveis. Verificar ELF64/AArch64, interpreter, `NEEDED`, versões GLIBC/GLIBCXX se presentes, ISA e resolução transitiva. Checar também o mínimo de kernel exigido pela libc do sysroot. Não usar `ldd` do host para concluir compatibilidade AArch64.
5. Não transportar libc/loader de Buildroot para `/lib` do Debian nem tentar consertar incompatibilidade com `LD_LIBRARY_PATH` global. Preferir reconstruir contra o destino. Emulação pode detectar falhas adicionais no host, mas não substitui teste nativo.

### Execução no aparelho — aprovada para listagem

O usuário autorizou esta Fase 1 e a conexão SSH. `/tmp` foi confirmado como tmpfs executável; transferência, teste e remoção ocorreram em diretório temporário aleatório, sem criar `/opt/muos`, units, symlinks ou permissões de hardware. O bloco abaixo permanece uma representação do ensaio; o runner efetivamente usado está no relatório.

```sh
# Representação do teste concluído; o runner usa diretório aleatório.
# Rodar como usuário comum, com ambiente de bibliotecas controlado.
env -u LD_PRELOAD -u LD_LIBRARY_PATH MUOS_RUMBLE_STRENGTH=0 \
    /tmp/muos-r35s-probe/muinput --list-devices
```

**Resultado esperado:** saída com IDs upstream, incluindo `rk-g350-v`/`rk-pixel-2`, e status 0, sem R35S enquanto não houver backend novo. Não é esperado detectar o aparelho nesse modo.

**Aprovação:** registrar saída/status, hash e ausência de erros de loader, símbolos ou instrução ilegal. **Limite explícito:** comprova apenas esse caminho de execução; não valida evdev, uinput, SDL/GLES, áudio, menu, boot ou o ABI de outro rootfs. Não executar `--foreground`, `--test` nem forçar `--device rk-g350-v` como extensão automática desse teste.

**Reversão:** remover somente o diretório temporário criado para o ensaio, mediante escopo previamente autorizado. Não interromper ES nem alterar boot. Se aparecer falha ELF, voltar à preparação de sysroot; não instalar bibliotecas no aparelho para fazer o binário passar.

## Fase 2 — Validar tela e controles separadamente

**Estado atual:** testes separados executados. O musplash precisou de fallback `pread/pwrite` porque `mmap` do fb0 retornou EINVAL; a adaptação está em `port/patches/`. SDL/KMSDRM/GLES funcionou a 59,90 fps em 30 segundos. O backend `rk-r35s-p0` foi testado com uinput real e nomes privados em mount namespace. Todas as direções/retornos e liberações foram cobertos. A sequência estrita normalizada registrou L3 duplo uma vez; um clique de conferência produziu um único par, sem estabelecer a causa. Por decisão do usuário ao iniciar a Fase 3, tratar essa ocorrência isolada como margem de erro e priorizar a investigação se reaparecer; preservar os dados brutos e o resultado estrito original. Não foram iniciados menu completo, testes de brilho/blank ou firmware.

### Tela: primeiro pixels, depois SDL/GLES

Após confirmar ABI, preparar um teste temporário de `musplash` framebuffer, com imagem conhecida e orientação marcada. O utilitário nativo muOS oferece `-i`, `-f`, `-r` e saída sem `--wait` (`module/musplash.c:172–194`). Ele pode confirmar caminho fb, cor, geometria e orientação, mas não testa KMS/EGL. Também pode fazer unblank; isso é mudança de estado do display, portanto requer um ensaio autorizado e plano de restauração, não faz parte da fase 0.

Em seguida, teste pequeno SDL2 que crie janela/renderer GLES2 acelerado com vsync e reporte driver, renderer, resolução e fps. Código novo eventual em `port/`, build em `build/`. Escolher o backend SDL depois de inventariar o que o Debian fornece; não presumir KMSDRM disponível por existir DRM. Confirmar EGL/GBM/libmali coerentes com o driver kernel. Um fallback software pode ajudar a localizar falhas, mas não satisfaz sozinho o caminho exigido pelo frontend atual.

Coordenar acesso exclusivo à tela apenas quando necessário e autorizado; registrar como restaurar o serviço ES e a tela pelo mesmo caminho de controle. Não executar o `sysinit` muOS para obter um display.

**Critérios:** imagem 640×480 correta, cores/orientação estáveis e frame pacing mensurável; SDL/GLES inicializa e apresenta quadros repetidamente. Confirmar refresh real; não herdar `60.303` do G350 ou `60.082` do Pixel. Ensaios de blank/brilho só depois de confirmar máximo e escala (DTB BSP local declara 160; comum muOS usa 255).

### Controles: capturar antes de adaptar

Capturar códigos e ranges reais com serviços atuais conhecidos. O DTB dArkOSen sugere HAPPY1/2 para Select/Start e HAPPY3/4/5 para L3/R3/Fn, mas o kernel ROCKNIX emite Select/Start/Mode diretamente. Definir o backend conforme o kernel escolhido; não compartilhar mapa cegamente entre stacks.

Depois da captura, criar perfil próprio no código de port: board ID, source name, mapeamento de teclas/eixos, endpoints power/volume, identidade virtual e GUID. Reaproveitar o backend evdev portátil com o menor patch necessário. Manter rumble desativado até comprovar hardware/driver. Não copiar transformações de eixos G350 sem medir centro, sentido e faixa dos dois sticks.

**Critérios:** um evento lógico por pressão; releases corretos; todos os botões e quatro eixos cobertos; sem controles duplicados ou hotkeys de outro serviço; saída limpa libera fontes/uinput. Validar power separadamente sem permitir desligamentos durante a captura. O teste de CLI da fase 1 não cobre esses critérios.

## Fase 3 — Primeiro menu muOS em bancada temporária

**Estado: recorte funcional validado, com ressalva dos recursos sonoros.** O `muxlaunch` nativo apresentou e navegou, incluindo A/B/Fn e seleção de Informações sem executar submenu. O mapping SDL foi corrigido por índices reais e GUID com CRC. Após a recuperação da raiz Btrfs, três ensaios de áudio validaram navegação/confirmação audíveis com ganho128, Fn/B com WAV de controle e encerramento sem cortar o último efeito. Serviços e mixer foram restaurados; raiz `rw`, kernel sem taint e contadores em zero antes/depois. Os WAVs originais da ajuda continuaram inaudíveis no speaker; a substituição foi apenas diagnóstica e o pacote padrão preserva os originais. Detalhes na [primeira sessão](phase3-native-menu.md) e na [retomada](phase3-audio-resume.md). Os timeouts MMC anteriores continuam sem causa determinada; musplash/mmap permanece excluído, conforme a [interrupção](phase3-storage-stop.md) e a [recuperação](storage-recovery.md).

**Pendência específica:** escolher/adaptar sons de abrir/fechar ajuda que sejam audíveis no speaker, sem considerar a troca temporária por confirmação uma solução de produto. A concentração em graves dos WAVs é hipótese apoiada pela análise do conteúdo e pelo controle comparativo; resposta acústica, EQ e fones não foram medidos. O corte no encerramento foi corrigido somente no executor de diagnóstico, com espera limitada de canais e margem para o buffer ALSA. O fluxo positivo do supervisor passou; o disparo independente do timer continua não exercitado. O recorte mínimo não inclui frontend completo, volume/brilho reais, energia ou firmware.

**Objetivo:** validar frontend real no R35S antes de construir firmware. A instalação dArkOSen funciona somente como bancada temporária; não é o produto final.

Preparar staging com config comum+override R35S, varstore, libs próprias, LVGL/PlutoSVG/SDL e dependências transitivas, idiomas, fontes, tema e diretórios de conteúdo/runtime mínimos. Os componentes completos também puxam vídeo, terminal, libretro e `mugl`; definir um recorte de build explícito no código do port, evitando prometer que o alvo global de Makefile será mínimo (matriz E8).

Auditar chamadas do módulo escolhido antes de executá-lo: existem caminhos absolutos para `/opt/muos` e `/run/muos`, hotkeys, brilho, áudio e energia. Overrides `MUOS_CONF_*` e `MUOS_RUN_DIR` existem no varstore, mas não relocam tudo. Escolher entre pequenos ajustes de path em `port/` e ambiente isolado/mount namespace, documentando quais writes e dispositivos serão permitidos. Não criar uma árvore muOS permanente sobre o Debian para contornar isso.

Começar com menu/mensagem e navegação sem lançamento de emuladores, desligamento, USB gadget ou formatação. Incorporar `muinput` validado e depois áudio; mapear mixer/rota/sink do RK817 e decidir como isolar PipeWire de serviços de áudio existentes. Não aplicar `asound.conf` do muOS ao `/etc` do sistema instalado.

**Critérios:** frontend apresenta e navega, sem controles duplicados; eventos e áudio funcionam; não há alteração persistente fora do staging autorizado; ES retorna ao encerrar. Registrar duração, CPU/RAM, falhas e limitações. Esse resultado valida o sysroot Debian de teste, não o futuro rootfs do firmware.

## Fase 4 — Fechar a base do firmware autônomo

**Estado: iniciada em 24/10/2026, ainda em andamento.** U-Boot, kernel/DTB e ext4 próprios Panel 0 já deram boot. [B01](phase4-ext4-diagnostic.md) aprovou gpio_keys e S90/storage; [C01](phase4-service-diagnostic.md) aprovou BusyBox PID 1 e a cadeia selecionada udev/D-Bus/S90/S95 input/S96, com mapping e parada, UI/áudio desativados. Logs e fsck offline passaram; o dArkOSen voltou saudável. A base completa tem 284 ELF userspace + 555 módulos; C01 acrescenta um executor diagnóstico. Essa prova não aprova rcS completo, renderer/áudio/UI no kernel próprio, energia/shutdown ou conteúdo. Há avisos de urandom antes da inicialização do pool, a tratar na integração de seedrng. A ajuda original permanece pendente. Os parágrafos seguintes preservam marcos intermediários e seus limites.

### Escolha do conjunto kernel/DTB/GPU

| Alternativa | Vantagem | Custo/risco | Condição para escolher |
| --- | --- | --- | --- |
| Base BSP próxima ao dArkOSen | Referência do hardware atualmente funcional e DTB Panel 0 já disponível. | Kernel antigo, fonte/config exatas e módulos precisam ser reconstruídos; stack GPU pode exigir userspace acoplado. | Obter fonte/config/patches/licenças e demonstrar reprodução + boot em cartão separado. |
| Base próxima ao ROCKNIX | DTS R35S/R36S, recipes e mecanismos de painel explícitos, kernel moderno no snapshot. | Novo conjunto de bindings, drivers, áudio/input e GPU; não comprovado no Panel 0 do usuário. | Comparar sequência/timings e reconstruir kernel+DTB+GPU coerentes; validar painel e controles fisicamente. |

**Decisão adotada para a investigação:** partir do BSP conhecido do dArkOSen para reduzir variáveis de bring-up, sem obrigação de mantê-lo no produto final. A fonte indicada permitiu uma candidata própria com configuração explícita. Foi recuperada uma cópia de configuração escondida sob o `/boot` FAT, coincidente com os recursos da prova; o commit exato e a reprodução do binário instalado continuam não comprovados. Se proveniência, licenças ou estabilidade da candidata não puderem ser fechadas, avaliar ROCKNIX com teste próprio. A compilação e a comparação estática não aprovam runtime de nenhuma das novas bases.

O overlay genérico do ROCKNIX é opção de migração de descrição de painel, não substituto universal de DTB: conversores podem alterar flags e sintetizar modos. Preferir apenas o modo confirmado inicialmente; comparar init/exit, reset, delays, alimentação, polaridades e timings. Não copiar o DTB BSP inteiro para um kernel mainline.

### Rootfs e init

**Continuação concluída neste recorte:** sysroot/rootfs headless compilados offline,
auditados e empacotados. O probe ABI passou em QEMU Cortex-A35 e nativamente
com loader/libc próprios em tmpfs, preservando o Debian. Há controlador retomável
e coleta de licenças/fontes. Isso não é teste de boot nem aprovação do init completo.
Estado, contratos de init e comandos do checkpoint inicial: [userspace da Fase 4](phase4-rootfs.md). O perfil ativo passou ao [core/áudio](phase4-core-audio.md), com 248 ELF e staging extraído da imagem ext4 finalizada. Buildroot é proprietário de eudev/D-Bus e S95muos-core prepara cache/áudio; o sysinit muOS completo permanece desligado. O teste do daemon com uinput real e o primeiro menu com a SDL nova passaram; sua ativação no perfil de produto aguarda init e serviços completos.

**Primeiro incremento executado:** [defconfig próprio](../../port/device/rk-r35s-p0/phase4-rootfs.defconfig), somente para bring-up sem gráficos. Usa headers da mesma revisão BSP, série4.4, separados do compilador antigo usado no kernel. O Kconfig confirmou as opções e o incremento seguinte gerou a imagem ext4 de 512 MiB; o checkpoint inicial não incluía payload muOS. O incremento core posterior incluiu somente utilitários/cache/áudio. A integração completa de PID1/rcS/rcK com `sysinit`/`shutdown`, os providers GPU/SDL e os demais comandos necessários continuam pendentes. Não tratar essa configuração como receita oficial do rootfs muOS.

Localizar a receita oficial e o defconfig do rootfs/toolchain muOS, hoje não identificados nos três repos. Se for preciso montar uma base nova, especificar conscientemente libc, init, udev, D-Bus, PipeWire/WirePlumber/plugins ALSA, SDL/EGL/GLES, utilitários de shell, firmware e versões. Verificar cada comando exigido pelos scripts, não só as dependências C.

Foi encontrada posteriormente uma [referência histórica adicional](phase4-historical-rootfs-lead.md), `cmclark00/mustardroot_external`, com defconfigs e pacotes. Seu vínculo com o processo oficial atual e as licenças por arquivo ainda precisam ser verificados; ela é uma pista de comparação, sem substituir o SDK próprio ou fechar a reprodução do rootfs atual.

Reproduzir o contrato muOS `/opt/muos`, `/run/muos`, configuração comum+board e conteúdo, com `/sbin/init` corretamente integrado a `sysinit` e shutdown. Reconstituir `/etc/inittab` ou mecanismo equivalente a partir de evidência; não inferir a imagem inteira pelo nome de um script.

Para a primeira imagem independente, preferir raiz ext4 e boot FAT conforme referências RK muOS, com área de ROM definida separadamente. Btrfs no aparelho atual é dado a preservar, não tarefa de conversão. Definir labels/UUIDs e conferir mapeamento U-Boot/Linux antes de fixar devices. Recompilar os componentes para esse novo sysroot e repetir a inspeção ELF e testes; aprovações no Debian não são transferíveis.

**Critérios:** manifesto reproduzível de fontes/patches/licenças, sysroot/toolchain fixados, init e dependências completos; kernel/DTB/módulos do mesmo build; rootfs inicializável em ambiente de teste quando aplicável. Nenhum blob sem origem/licença resolvida entra em release.

**Áudio:** ALSA/S16, ALSA/S32 e PipeWire produziram três grupos igualmente baixos e audíveis, com Playback 95,95 amostrado no PCM ativo. Não foi observada diferença específica do PipeWire nesse recorte; volume dos sons reais continua pendente ([comparação](phase4-core-audio.md)).

**Input nativo do sysroot próprio:** criação uinput legada, grab/isolamento da fonte, sequência dos controles e remoção/liberação passaram. Foram verificados D-pad, A/B/X/Y, ombros/gatilhos, Select/Start/Fn, L3/R3, volume e sticks, sem SYN_DROPPED ou teclas presas. L3 teve um único par; a ocorrência anterior não reapareceu. Mapping SDL, Power e boot do daemon continuam não testados ([relatório](phase4-native-input.md)). O default core ainda mantém input desligado.

**Gráficos:** a [candidata Buildroot original](phase4-graphics.md) passou no host mas falhou antes de EGL, por Mali UK 10.6 versus kernel 11.7. A candidata BSP também usa handshake 11.7; a referência anterior 10.6 era um header legado. Foi identificada a origem Hardkernel do blob r13p0 instalado: o usuário forneceu o ZIP original e seu hash conferiu com a receita Batocera; o membro AArch64 é idêntico ao instalado. Um [overlay de diagnóstico](phase4-r13-runtime.md), sobre o userspace próprio, passou em carregamento QEMU, contexto EGL/readback e SDL/KMSDRM nativo a 59,884 fps, sem falhas de renderização e com confirmação visual. Isso não constitui uma reconstrução da imagem Buildroot nem valida seu boot. O ZIP não contém EULA: redistribuição e integração ao firmware permanecem pendentes.

**Menu no userspace próprio, 25/10:** dependências e muxlaunch foram recompilados contra o SDK Buildroot. QEMU/link, 274 ELF AArch64 na base e fsck passaram. O overlay privado r13p0 executou o primeiro menu com texto/navegação/A/B/Fn e áudio SDL/PipeWire, confirmados pelo usuário; a confirmação de A drenou sem corte. O áudio foi medido com Playback 153,153, software em unity e PCM S32_LE/44100 Hz. Ajuda usou WAV de controle, e scripts de volume/brilho ficaram interceptados. A coleta detectou restauração inicial para 95,95 após a sessão: o nível foi reparado e uma regressão automática passou com a nova conferência do snapshot após subir os serviços ([relatório](phase4-menu-own-rootfs.md)).

**Decisão de licenças, 25/10:** por solicitação do usuário, r13p0 e futuros componentes com termos pendentes ficam restritos ao uso privado durante o desenvolvimento. Registrar cada pendência em [pending-licenses.json](../../port/packaging/pending-licenses.json) e gerar **ao fim do projeto** `docs/licenses-to-resolve.md`, para uma única rodada de resolução. Não encaminhar consultas individuais agora. A publicação continua condicionada aos termos aplicáveis; a decisão não equivale à obtenção de uma licença do fornecedor.

**Provider e storage privados, 25/10:** o [novo incremento](phase4-private-foundation.md) integrou r13p0 à própria receita Buildroot para SDK/target e reconstruiu a imagem inteira. A transformação de SONAME/strip foi reproduzida e conferida, sem substituição posterior de Mali no staging. Passaram 281 ELF AArch64, fsck, contrato GBM e carregamento QEMU das bibliotecas do frontend ampliado. O contrato de uma única mídia (`/userdata` → `/mnt/mmc` → `/run/muos/storage`) passou nativamente em namespace/tmpfs, incluindo rollback, mount preexistente, detecção de bind errado e start/stop. A guarda S95 impede iniciar core sem storage íntegro. O primeiro resultado foi invalidado por ausência de `stat`; o fragmento BusyBox e a checagem foram corrigidos antes da repetição aprovada. Isso ainda não testa persistência em ext4 após reboot, coldplug, SD2 ou autostart do frontend.

**Frontend ampliado e ajustes reais, 25/10:** o [ensaio seguinte](phase4-full-frontend.md) gerou mapping SDL nativo e521 associações pelo `assign.sh` original. O frontend sem wrappers abriu e voltou entre módulos de Informações, Configurações, Exploração e outros menus vazios. EGL/readback e confirmação visual passaram. Com `muhotkey` e os helpers originais, volume100→95→100 e brilho80→75→80 passaram; o teste manual revelou dois passos de volume por ler a fonte física e a virtual. O [patch0006](../../port/patches/0006-frontend-r35s-normalized-volume.patch) mantém só o caminho virtual nesse board. A repetição confirmou um passo por toque, brilho e áudio. Ajuda usou WAV de controle; Power/idle/hold ficaram fora do recorte de hotkeys. Todas as sessões terminaram coletadas/removidas, com mixer igual ao snapshot, brilho80, serviços ativos, taint 0 e contadores Btrfs 0.

**Integração concluída no host, 25/10:** patch0006, scripts/manifesto e mapper foram incorporados pelo overlay Buildroot a partir do checkpoint aprovado. A nova imagem tem282 ELF AArch64; QEMU/link/GBM, recursos, comparação dos oito ELF incorporados e fsck passaram. Autostart segue desligado, sem novo ensaio no console ou boot. Estado e comandos estão no [ponto seguro de retomada](phase4-resume-checkpoint.md), criado para encerrar esta rodada antes do limite de uso.

**Espera, supervisão e autostart, 25/10:** o [novo adaptador](phase4-init-services.md) liga S90→S95→S96→S99. S96 espera o `muinput` real e valida o mapping; S99 exige novo first_paint e supervisiona frontend/hotkeys, sem loop de crash. Falhas, stop idempotente, perda de input, saída antecipada e helpers destacados por setsid/duplo fork passaram em namespace. As sessões com UI real confirmaram tela, submenus, áudio e volume/brilho; o som original da ajuda segue pendente. A imagem reconstruída tem283 ELF e autostart configurado, com auditoria/QEMU/fsck aprovados. Não houve mudança do startup Debian nem boot da candidata. Mixer/brilho/serviços foram restaurados e os temporários removidos.

**Módulos/firmware integrados no host, 25/10:** a [nova imagem](phase4-modules-firmware.md) tem 284 ELF userspace + 555 módulos ET_REL AArch64. Vermagic, dependências declaradas, símbolos via System.map, índices kmod 33, hashes na ext4, QEMU em modo de consulta e fsck passaram. O dongle observado 0bda:c820 resolve 8821cu e btusb/btrtl; dois firmwares Bluetooth Debian com termos identificados acompanham avisos, e rtk_btusb tem autoload bloqueado. Não houve carregamento de módulos ou boot candidato; Wi-Fi/BT, coldplug e infraestrutura de rede continuam pendentes.

**DTB U-Boot Panel0, 25/10:** o [delta próprio](phase4-uboot-panel.md) compilou e passou na comparação de 37 propriedades de display/backlight e propriedades selecionadas de providers com o DTB instalado. Fonte U-Boot completo e quatro payloads de receita foram fixados; o executável ainda não foi construído. A inspeção localizou seleção de DTB por ADC da família RG351 e recuperação automática que escreve SPI e pode apagar setores SD. Esses caminhos precisam ser removidos da candidata de teste; não foram executados.

**Executável U-Boot SD, 25/10:** o [monitor próprio](phase4-uboot-sd.md) compilou e passou em ELF, defaults extraídos do executável, macros/configuração, comandos/mapa e DTB externo. Autoboot está desligado; ambiente só em RAM e panic sem reset. Os caminhos identificados de recovery SPI/erase, OP-TEE client/RPMB, ADC e testes de fábrica foram excluídos deste perfil. Packers GPL construídos do fonte produziram contêineres privados; CRC, hashes, payloads, backups e limites de regiões passaram em parser independente e provas negativas. O trust reproduziu exatamente o instalado. Não houve acesso ao console ou escrita de mídia; não é firmware pronto para boot.

**Primeiro boot nativo do monitor, 25/10:** a [reserva explícita do DTB](phase4-memory-monitor.md) protege sysmem e LMB de boot, com fixture dos alocadores nativos/UBSan e provas negativas aprovadas. O monitor visual foi escrito no secundário de 128 GB por autorização do usuário; releitura integral passou. O aparelho iniciou o U-Boot próprio e mostrou texto correto, RAM top `40000000`, vídeo `3de00000–3fff0000`, U-Boot `3dd08000`, stack `31cfd580` e Control DTB `01e00000`. O usuário confirmou Power longo desligando e retorno normal ao dArkOSen no cartão original. Após reconectar o Wi-Fi, SSH confirmou Image inalterado, taint 0, cinco contadores Btrfs 0 e serviços ativos; o cartão secundário está sem montagem. Isso valida somente o monitor neste Panel 0; a imagem de teste não contém Linux/rootfs.

**Primeiro boot Linux próprio aprovado:** o [primeiro boot Linux](phase4-linux-diagnostic.md) tem initramfs mínimo do sysroot próprio, console tty0 e logs vinculados ao CID do cartão de teste. U-Boot verifica tamanho/SHA-256 antes de booti. Arquivo/ABI/QEMU, fixtures de cartão, reservas, ELF/defaults, FAT/readback e provas negativas passaram. O secundário de 128 GB foi preparado e relido integralmente. O usuário confirmou a tela e os logs recuperados mostram kernel próprio, init em RAM, console e taint 0; a saúde do dArkOSen foi conferida após o retorno. Avisos selecionados também aparecem no sistema instalado, sem aprovação de todos os recursos. `gpio_keys` é módulo e não foi carregado neste recorte. A ext4 completa e o frontend continuam fora deste ensaio.

**Ext4 diagnóstica aprovada:** [B01](phase4-ext4-diagnostic.md) iniciou pelo kernel próprio, carregou gpio_keys e verificou S90 start/status/stop. Corrigido padding de MAJ:MIN com findmnt -rn. Root voltou ro, logs foram recuperados e fsck offline/saúde original passaram. Não executou init BusyBox ou rcS completo.

**Init/serviços C01 aprovados:** [ensaio nativo](phase4-service-diagnostic.md) confirmou BusyBox PID 1, coldplug GPIO, RPC D-Bus, S90/S95/S96, muinput e mapping, com UI/áudio disabled. A sequência parou e devolveu root ro; DIAG03, fsck e saúde do dArkOSen após retorno passaram. A prova vale sem dongle Wi-Fi e para esse recorte, não para o rcS completo.

**C02 aprovado no recorte diagnóstico:** [seedless e persistido](phase4-entropy-diagnostic.md) passaram com consumo/rotação nativos. Logs por boot reproduziram a parada anterior: prazo de 5 s insuficiente. Correção 5 → 60 s permitiu o boot persistido na primeira tentativa, pronto após 7114 ms; aviso conservador do próprio seedrng preservado, sem avisos prematuros de consumidores. Input/parada/root ro/fsck e retorno saudável passaram. Não aprova qualidade criptográfica, rcS completo ou shutdown normal.

**C03 gráfico aprovado:** [EGL/SDL no kernel próprio](phase4-native-graphics.md) passou na primeira tentativa, com readback, 640×480 acelerado/vsync, 59,630 fps em 30,002 s e confirmação física. Modo DRM e console restaurados, entropia persistida/input/parada/root ro/fsck/retorno saudáveis. Provas pré/pós-boot separadas; não houve troca de bibliotecas ou bootloader/kernel.

**C04 frontend aprovado:** [primeiro boot supervisionado](phase4-native-frontend.md) passou com S99/supervisor/frontend reais, first_paint novo e pai correto, navegação de menu/submenus/ajuda e retorno ao diagnóstico. Sessão configurada para 75 s, sem áudio/hotkeys; stop pelo serviço, configuração temporária removida, modo DRM/root ro/fsck e retorno saudáveis. Não habilitou UI permanente nem alterou bibliotecas/binários.

**C05 áudio básico aprovado:** o [ensaio de áudio](phase4-native-audio.md) resolveu o FD gravável do mulog que impedia root ro e a identidade ALSA sem ID_PATH que impedia publicar o sink. SPK permaneceu inaudível em95 e157, apesar de PCM válido. Na revisão5/BOOT0012, SPK_HP com157 tornou os três bipes audíveis, confirmados pelo usuário. PCM S32_LE/stereo48k, restauração SPK/95 e software0,35, snapshot ALSA pré-core, parada/logger/debugfs/root ro/fsck e retorno saudável passaram. Provas pré/pós-boot separadas; nenhum binário/kernel/DTB alterado. A rota/ganho foram temporários; perfil persistente95/SPK ainda precisa de integração coerente. Calibração final, frontend sonoro, hotkeys e fones não estão aprovados nesse recorte.

**C06 frontend sonoro aprovado:** [revisão4/BOOT0017](phase4-native-frontend-audio.md) confirmou menu/submenus, A/B/Fn e navegação audíveis com adaptação exclusiva de navigate.wav (+8,8dB, pico30000, sem clipping no arquivo). SDL/PipeWire S32_LE/estéreo44100, SPK_HP/157/unity; treze hashes/ALSA/cache/binds/logger/rootro/entropia/input/fsck e saúde stock passaram. Ajuda usa confirmação de controle. Calibração final, ajuda original, hotkeys/fones/energia e estabilidade longa permanecem pendentes.

**C07 Wi-Fi/SSH aprovado no BOOT0018:** [integração diagnóstica](phase4-network-ssh.md) confirmou ejeção real0bda:1a2b→c820,8821cu/wlan0, associação/DHCP, fingerprint comparado pelo usuário, chave fixada, autenticação SSH e transferência em RAM. Todos os estágiosRC0, RNG persistido/refresh/stop, rootro/FAT desmontado/taint0 e contagem de erros selecionados0. R0 falhou por prazo200 acima do máximo120; r1 separou USB75/rede120 e passou14 checks. Provas negativas/positivas separadas; nenhuma credencial/seed/chave privada exportada. Os resultados seguintes ampliam esse recorte: coleta offline e C08 passaram; reboot ainda exige investigação. Ver estado atual no checkpoint.

**C08 menu com rede aprovado:** o [ensaio combinado](phase4-network-frontend.md) reutilizou o frontend/áudio C06 com D-Bus/storage/core/input próprios, preservando Wi-Fi/SSH/udev do C07. Confirmação manual e repetição automática passaram; PID/starttime da infraestrutura,13 hashes, mixer/cache/DRM, remoção do socket D-Bus e rootro/taint0 conferidos. Um falso alarme do observador com workerudev foi corrigido e preservado separadamente. Oito cenários de cadeia e sete de identidade passaram; código foi executado só em RAM/namespace privado. Reboots19/21/24 alcançaram Linux, mas a interface Wi-Fi ficou sem driver com c820 retido. R2 reset/reprobe não resolveu. C07r3 recuperou SSH no BOOT0024 por uma retirada/reinserção física, mantendo rootro/chave e preservando relatório negativo e RECOVER.TXT separados. Frio22/23 passou; rootro/taint0/FAT desmontado e51 hashes foram conferidos. O unload de8821cu antes do25 foi comprovado e também não resolveu; recuperação física repetiu sucesso. Nenhum novo shutdown persistente foi adotado. Não aprovar reboot automático a partir da recuperação física.

**Próximos incrementos:** Wi-Fi após warm reboot agora passou no37/38/39 com política Wi-Fi-only que bloqueia aliasautoloadbtusb (detalhesC18 abaixo). Priorizar dadosrw com rootglobalro, defaults uma vez e persistência volume/brilho antes do arranque permanente do menu; manter o pacote opt-in nas receitas. Não reabrir reset/reprobe/unload/configuração/cicloDWC2 sem regressão concreta. Bluetooth USB continua desativado/não qualificado; calibração, poweroff físico/Power/suspend, conteúdo, fones e longa duração seguem pendentes. Acesso e estado no [checkpoint](phase4-resume-checkpoint.md); reutilização de base e alternativa G350 em [phase4-base-choice.md](phase4-base-choice.md).

**C09 controles nativos medidos e restaurados:** [volume/brilho com SSH](phase4-network-controls.md) passou usando helpers e muhotkey/S99 reais em sessãoRAM. Quatro toques produziram volume100→95→100 e backlight80→75→80; helpersCLI, mixer/18hashes/cache/pasta de volume/DRM/brilho, rede/udev e rootro/taint0 passaram.33probesSSH,30comUI,61,99s simultâneos. Usuário percebeu dois passos visuais no brilho; preservada ressalva: fonte converte0..160 em porcentagem inteira50→46→50, sem captura que explique a percepção. Barra de volume100 representa software, codec157 fixo; calibração acústica pendente. Nenhuma UI/perfil/init permanente foi habilitado. Candidata permanece com SSH após recuperação física no25; fsck offline pós22..25 ainda pendente.

**C10 perfil/receita consolidados:** [perfil reproduzível](phase4-runtime-profile.md), pacote muos-r35s-profile e hook pós-overlay explícito geram os dados aprovados sem perder defaults para o overlay antigo. Dez checks de determinismo/instalação/guardas/rollback e Kconfig isolado passaram. No kernel próprio,21 hashes pré-core,19estáticos e valores pós-setters passaram; menu/sons/submenus confirmados, SSH simultâneo e restauração aprovados. Primeira tentativa parou por LF dos valores regravados; prova negativa e correção do verificador preservadas. Licenças/fontes dos WAVs acompanham payload. Não houve imagem completa, instalação permanente ou UI autostart. Próximo: lifecycle/init que consuma esse perfil sem depender da bancada C06/C09, com contrato de persistência.

**C11 ciclo independente aprovado:** [serviço start/status/stop](phase4-session-service.md) consome C10 sem executores C06/C09 e preserva rede/udev/RNG. Oito casos de cadeia/dez de controle, receita de cinco utilitários próprios, loader/QEMU e Kconfig isolado passaram. Três gerações nativas: stop explícito/idempotência, lease30 sem confirmação visual e repetição lease60 confirmada, com firstpaint/identidades novas e cleanup0/status3. Perfil21 hashes e21 originais, mixer/cache/brilho/DRM/volume-store e SSH/ro/taint0 passaram. Fonte final limita log acumulado; único delta cp→tail verificado e cinco ELF idênticos ao testado. Sem instalação permanente/UI autostart ou imagem inteira. Próximo: coordenador único de init/shutdown e persistência, resolvendo duplicação do rcS antes de enabled1.

**C12 adaptadores e barreira aprovados:** [coordenador único](phase4-boot-coordinator.md) ganhou adaptadores/guards reais, controlador, receita opt-in e template inativo de inittab.20 fixtures de ordem e33 de controle/identidade/quiescência, instalação real, loader/QEMU e Kconfig isolado passaram. Na candidata, check-stop passou em idle, recusou enquanto C11 estava ativo e passou após stop0; usuário confirmou o menu. Perfil21/originais21, mixer/brilho/DRM/volume-store e infraestrutura SSH/udev foram preservados; rootro/taint0 e RAM removida. Nenhum boot/shutdown C12 ou instalação persistente foi realizado; enabled0/allow_power0. Próximo: wrapper diagnóstico/logs e recuperação física da rede com ownership C12 antes de ativar a seleção de init. Persistência continua false/volatile; política3 ainda força software100. BusyBox executa TERM/KILL após SHUTDOWN mesmo com erro: preflight precisa preceder o pedido ao PID1.

**C12 boot único e fallback aprovados:** [instalação/boot27](phase4-boot-once.md) passou com seletor opt-in que consome token antes do arranque; próximo boot28 confirmou C07 sem menu, sem trocar cartões.88 checks host (20+33+35), macro/shell/instalação dirigida passaram. Erro de caminho // no primeiro preflight foi interrompido antes de escrita e corrigido com regressão; prova negativa separada. Rede27 falhou inicialmente e recuperou com replug físico, RNG atual e novos PID/starttime/exe próprios. Menu90s/DPAD/A/B/Fn confirmados; áudio presente porém baixo com SPK_HP/157/software100, sem aprovação de calibração. Lease0/21+21 hashes/restauração/55 pré-requisitos/rootro/taint0 e relatórios FAT START/FINAL passaram, inclusive após reboot28. C12 segue instalado, mas token consumido/defaultC07; receita disabled0, configs da bancada opt-in, allow_power0. Sem kernel/DTB/bootloader/partições/libs/módulos alterados. Próximo: prova durável de preflight/shutdown antes do pedido ao PID1, depois persistência e sessão permanente. WarmWi-Fi e calibração permanecem abertos.

**C12 energia durável aprovada (reboot30→31):** [preflight/arquivo](phase4-boot-power.md) ganhou journal público PBEGIN/PREADY/PFAIL, sync/readback/unmount e checagem final antes do pedido ao PID1.116 checks host (20+32+35+29), macro/loader/shell AArch64 e atualização dirigida de cinco scripts passaram. Falha inicial do manifesto relativo disparou rollback0 com hashes/rootRO/rede restaurados; correção cd / e regressão preservadas. C07 e diagnóstico C12 incompleto recusaram energia64 sem parar rede. Boot30/lease90/restauração/coleta passaram; após reboot pelo controlador, C07/31 e os seis passosRC0 em PREADY foram comprovados por leituraRO da FAT. START/FINAL idênticos,55 pré-requisitos/todos os hashes/rootRO/FAT desmontada/taint0 e erros selecionados0. Token consumido/defaultC07/allow_power0; permissão do ensaio somenteRAM. Sem poweroff físico, Power/suspend, UI permanente, persistência, kernel/DTB/bootloader/libs/partições alterados ou novo fsck offline. Dongle precisou de replug em30 e31; resolver isso é a próxima prioridade explícita do usuário.

**C13–C15: warm USB localizado, correção ainda aberta:** [diagnóstico/ensaios](phase4-network-warm.md) confirmou no32 dez timeoutsUSB-110 lendo SYS_CFG2/0xfc, HALMAC54 antes da identificação do chip. Log4 temporário foi removido/log3 restaurado.33/SET_CONFIGURATION0→1 e34/lifecycle completo DWC2 ff300000.usb foram executados comRC0, mas não recuperaram driver/netdev; replug físico continuou necessário.37 checks host, shellAArch64 e todos os cleanups passaram. HelperUSB/tabela55/SHA anteriores restaurados, trials/tokens removidos; C07/34/rootRO/FAT desmontada/taint0/brilho80/erros selecionados0 e SSH fixado conferidos. Sem kernel/DTB/init/driver/perfil/bibliotecas alterados. Resultados negativos preservados, sem promoção permanente. Próximo: distinguir controle padrão/vendor e auditar estado antes do reboot; não repetir reset/reprobe/unload/configuração/ciclo do controlador como hipóteses novas. Não forçar identificação/efuse ou cortar VBUS sem comprovar circuito/consumidores.

**C16–C18: Wi-Fi quente corrigido na bancada com política reproduzível:** [controleUSB/isolationBT](phase4-usb-control.md) qualificou probeAArch64IN;35 mostrou controles padrão e vendor todos-110, recuperando após replug.36 retirouDWC2 antesPID1 com prova durávelRC0 e também falhou;24checks e cleanups passaram. Fonte revelou que btusb agenda inicializaçãoHCI mesmo semBlueZ. Blacklistaliasbtusb permitiu37/38 automáticos e, após promoção a pacote opt-in muos-r35s-wifi-only,39 também automático; usuário confirmou três reboots sem tocar no dongle. Macro real/Kconfigseparado/SDKbaseline,55 pré-requisitos/hashes/relatóriosFAT/SSHfixado/rootRO/taint0 e erros0 passaram. Só configmodprobe e licençaMIT persistem; trials/helpers/probes removidos e bytes originais restaurados. Kernel/DTB/init/perfil/módulos/libs não mudaram, sem imagem toda nova. Política bloqueia autoloadBTUSB desta imagem e foi medida só noPanel0/c820/kernelatual; Bluetooth/coldboot com pacote final/longa duração não qualificados. Próximo: dadosrw com rootro/preferências persistentes.

**C19 preparado com saldo limitado:** [preferências](phase4-preferences-preparation.md) ganhou store originalMIT tipado/atômico, defaults uma vez e recusa de corrupção/links/flags transitórias.16 fixtures AArch64/QEMU e teste nativo somenteRAM no39 passaram; binário/dados temporários removidos, brilho real80/rootRO/FAT desmontada/taint0/rede e55 hashes preservados. Sem integraçãoC11/C12, imagem nova, partições ou persistência habilitada. Inventário confirmou raiz512MiB e ausência de dados/p3. Próximo: mount ext4rw separado com rootglobalRO, depois dados reais e integração. Política3 e LOAD_SINK_VOLUME exigem tratamento explícito; S80 ainda restaura arquivosALSA na raiz. Não substituir isso por bind persistente indiscriminado.





A [cadeia instalada](phase4-boot-chain.md) tem trust.img idêntico ao ref dArkOSen, idbloader/U-Boot divergentes e base `5606e804ff-dirty`; sua reprodução exata continua desconhecida. A candidata própria usa fonte fixado, delta Panel 0 e empacotamento conferido, agora com boot real de monitor e Linux mínimo. Os payloads DDR/BL31/BL32 continuam privados, com termos pendentes no registro. A aprovação do diagnóstico não fecha o firmware completo; framebuffer mmap segue excluído por causa das falhas históricas. Os logs atuais e o retorno têm taint 0, sem erros MMC/I/O na busca documentada e contadores Btrfs originais zerados.

## Fase 5 — Imagem em cartão separado e bring-up nativo

Somente após autorização específica para escrever uma imagem em mídia explicitamente identificada. Preservar e retirar o cartão dArkOSen; não atualizar bootloader, reparticionar ou regravar o cartão original. Conferir caminhos de mídia, possibilidade de recuperação e comportamento de boot da revisão antes da escrita.

Produzir temporários em `build/` e artefatos finais em `dist/`. Documentar layout completo: tabela de partições, região reservada ao loader/SPL/DDR/firmware, offsets e proveniência de U-Boot, boot config, kernel, DTB e initramfs se necessário. Os offsets H700/A133 do `tool/device.json` não se aplicam. O preset Panel 0 exige DTB de U-Boot separado no fluxo dArkOSen; uma cadeia alternativa só pode dispensá-lo com validação própria.

Ordem dos testes na mídia de teste:

1. Bootloader → kernel → raiz → shell/diagnóstico; manter logs suficientes para diferenciar tela preta de falha de boot.
2. Painel, brilho conservador e recuperação de blank; input e saída limpa dos testes.
3. Frontend/varstore/storage prioritário; depois ALSA/PipeWire, bateria/carga, LEDs e power.
4. Lançamento e retorno de um core AArch64; só então ampliar emuladores/serviços e avaliar compatibilidade 32 bits se houver necessidade.
5. Shutdown e integridade de mounts; depois suspend/resume, áudio pós-resume, longa duração, carga e múltiplos ciclos de boot.

**Critério de firmware nativo:** cartão independente inicia diretamente o ambiente muOS AArch64, opera os recursos básicos do Panel 0 e desliga corretamente, sem depender de ES ou rootfs dArkOSen. Não declarar suporte geral a R35S/R36S a partir desse aparelho único.

## Fase 6 — Consolidação e ampliação de compatibilidade

Manter a matriz por placa/painel/kernel, com identificação explícita de genuínos/clones. Adicionar outros painéis somente com DTB/sequência proveniente de evidência e teste físico correspondente. Não “autodetectar” painel por um nome genérico de SoC.

Automatizar builds isolados e manifestos; conferir hashes, dependências, licença e tamanho das imagens; publicar limitações e procedimento de recuperação. Só automatizar updates depois de provar boot/partições e recuperação. Testes sintéticos e compilação permanecem evidência parcial; validação prolongada no hardware é necessária para estabilidade térmica, carga, áudio, controles e framebuffer/GPU.

## O que foi verificado na análise inicial

- Instruções locais, revisões HEAD, sparse checkouts e alterações preexistentes nos refs.
- Código/configurações muOS, preset e DTBs binários Panel 0, serviços dArkOSen via objetos Git, DTS/patches/recipes ROCKNIX, flags/dependências e licenças de topo/cabeçalhos relevantes.
- Decodificação em memória de propriedades FDT e hashes do par DTB Linux/U-Boot; confronto dos timings e mapas de input com as fontes.
- Consistência dos dois documentos e das referências locais, sem executar checks de upstream que compilam ou modificam arquivos.

**Atualização após Fase 3 e recuperação:** ABI/listagem, framebuffer com adaptação, renderer SDL/KMSDRM/GLES, uinput, menu nativo e áudio de navegação/confirmação foram exercitados. Fn/B reproduziram o WAV de controle e a confirmação ao sair terminou corretamente após ajuste do executor. A confirmação visual da Fase 2 é limitada pelos BUGs de memória em musplash encontrados posteriormente; esse teste não foi repetido. A bancada operou `rw`, com contadores em zero e kernel sem taint nos novos ensaios. Serviços, brilho80 e Playback157/237 foram conferidos ao final. Isso não comprova ausência de defeito físico ou estabilidade prolongada. A ressalva isolada de L3 permanece como margem de erro até eventual recorrência. **Pendências:** sons originais da ajuda no speaker, frontend completo/submenus, ajustes reais de brilho/volume, áudio prolongado/fones/pós-resume, bateria sob carga, shutdown/suspend, boot autônomo e reprodução da base de firmware/kernel/rootfs muOS.

**C19 ext4 nativo aprovado; C20 planejado:** [laboratório e dados](phase4-preferences-ext4.md) qualificou imagem16MiB em RAM/loop próprio/namespace privado com raizRO. Oito recusas host e nativo40 com init100/80→save60/75→unmount/remount→init/load60/75 passaram; mount ausente/backing incorreto/RO recusados, cancelamentoSIGTERMRC143 e cleanup/mountinfo global/55 hashes/rede/brilho80 íntegros. Imagem desmontada recolhida passou fsck offline; laboratório removido. Survey real e planner puro/oito gruposchecks prepararam p3 sem alterar bytes fora do slot478..493; nada gravado/formatado no cartão. Próximo: estação offline pelo leitor do Steam Deck oferecido pelo usuário, backup privado640MiB e writer/formatter/recuperação testados antes de qualquer alteração. Persistência real/C11/C12/permanente ainda desabilitados.

**C20 parcial seguro, leitor do Steam Deck:** [transação/retomada](phase4-userdata-offline.md) criou p3 após backup privado640MiB em dois hosts/fsckoffline, preservando o prefixo protegido exceto slotMBR. Formatação ainda não iniciada: guard confundia rc0 de PART_ENTRY_* com filesystem. Correção/probe/resume explícito e reparo limitado de root0777 (efeito do automounter doDeck)→0755 foram preparados;11IO+21protocolo/guardas, formatter/markers/fsckregular e cópia privada real de root passaram (5bytes, sem dados alterados). Pacote atualizado noDeck mashelperroot parado; usuário se ausentou,128 permanece noleitor/desmontado/R35Soff. Retomar helperlocal→inspect/resume/format/verify/correção/verify/stop antes de devolvercartão; novo store nativo e persistência por reboot ainda não testados. Backups/segredos fora dedist; original32preservado; integraçãoC11/C12/firmware continua off.

**C20 offline concluído:** [resultado/coleta](phase4-userdata-offline.md) confirmou noDeckIP17 ext4/MUOSDATA/markers, fsckoffline dos3volumes e root0755 restaurado. Alias whole-device/p2 tinha caches independentes: leitura0diferenças foi rejeitada e superada por auditorlocal com BLKFLSBUF apenas nos aliases do128. Readback fresco comprovou5bytes de modo/checksums inode2 e prefixo640MiB protegido, sem dados/FAT/boot alterados.11IO+21guardas+5cachechecks passaram; código futuro passou a sincronizar/reabrir aliases e recusar0bytes. Coleta offline-complete.xsay7jtk, backupantigo retido, cartão desmontado/helperoff. Próximo: retorno128 aoR35S/coldboot/55 hashes, store6075 real e reboot; runtime/C11/C12 persistente ainda off.

**C20 nativo/persistência no41→42 APROVADO:** [resultado](phase4-userdata-offline.md) confirmou coldbootC07/p3/root0755RO e55 hashes após retorno do128. Diagnóstico privado criou defaults100/80 uma vez, salvou60/75, preservou por unmount/remount/init/load e recusou ausente/RO. Reboot normalC07 sob preflight voltou42 e novo init/load exigindo registro existente preservou60/75; cleanup/montagensglobais/rootRO/brilho80/rede/taint0/55 hashes/erros selecionados0 passaram. Stages data-native.7cc5i4ee e jc8ptzxk. Só armazenamento foi aprovado; valores não foram aplicados ao hardware e runtime/firmware permanece disabled. Próximo: integração opt-in C11 com RAM overrides/policy0/slot e audit de writers ALSA/S90, depois lifecycle soblease; não repetir USB nem promover menu permanente.


**C21 opt-in nativo aprovado no recorte60/75:** [integração](phase4-preferences-session.md) adicionou o adaptador C11 com validaçãoC10/21 antes de overridesRAM/policy0/slots coerentes, dados p3 privados e isolamento dos writers ALSA/WirePlumber/HOME/log. Gerações2→3 no boot42 carregaram/aplicaram/checkpointaram60/75 com raizRO em ambos namespaces, restauraram mixer/brilho80/DRM/cache/hashes e desmontaram p3; pacoteRAM removido.14 fronteiras+8cadeia/10controlador e receita/ABI/BusyBox passaram. Provas dist/phase4/preferences-session-native. Save do par igual evita rewrite; próximo teste deve ALTERAR pelos botões, recarregar e fazer reboot controlado. Default opt-in0/C12inativo/menu permanenteOFF. Deck já limpo: cinco diretórios, backup remoto e chave da tarefa removidos após conferir backup privado local; recibo dist/phase4/deck-cleanup. Não pedir cartão/leitor nem repetir preparação offline.


**C21 edição física e reboot42→43 APROVADOS:** [qualificação](phase4-preferences-physical.md) mediu botões reais60/75→55/75→55/70, checkpoint com inode novo e segunda sessão recarregando/aplicando55/70. Após reboot NORMAL C07, um novo runtime C21 privado no43 aplicou volume0.55/brilho70 novamente. Raiz privada/globalRO, restauração, p3desmontada,55 hashes/rede/taint0 e assinaturas de erro0 passaram; pacotesRAM removidos. Provas separadas preferences-session-physical-edit, preferences-session-reboot e preferences-session-reboot-transition preservam as anteriores. Valor atual55/70: não repetir diagnóstico C20 hardcoded60/75. Próximo: consistência do pacote/receita/dependências para bootC21RO; adapter ainda depende de card-guard em muos-boot. Não rearmarC12 antigo/menu permanente. Nenhuma mudança no cartão original32 nem novo uso doDeck.


**C22 pacote sem dependência circular de boot APROVADO:** [pacote](phase4-session-package.md) moveu a responsabilidade por carregar card-guard para cada chamador, adicionou manifesto15 ao start opt-in e declarou util-linux basic/mount.8fixtures de integridade,4casos KconfigREAL e receita/reinstalação/ABI/BusyBox passaram; SDKbaseline intacto e6ELF iguais aos C21. Sessão43/run-0002 com muos-boot oculto no worker carregou/aplicou55/70 e parou/restaurou limpa; caminho global/55 hashes/rootRO/p3desmontada/brilho80/rede/taint0 preservados e RAM removida. Provas session-package-independent e session-package-kconfig. Sem instalação/reboot/token novo; C21 físico/reboot não repetidos. Próximo: composição/conferência do rootfs candidato e seus manifests/defaults após overlays, antes de desenhar instalação e novo boot de uso único/recuperaçãoC07. Não rearmarC12 antigo/menu permanente.


**C23 composição privada HOST aprovada:** [rootfs](phase4-rootfs-candidate.md) compôs ext4ROOTFS512MiB da base C07 limpa com macros reais C10/C22/Wi-Fi-only e hook final. Fundação89 gerada após overrides, perfil21/payload15 válidos, defaultsoff/C07direto. Corrigidos contratos de bootstrap(audio1 passivo C10) e contadorfactory0. Fsck/releitura integral/raiz0755,305ELF+555módulos/172loadersQEMU e14 fixtures passaram; SDK/base preservados. Imagem só embuild, provas semblobs/segredos em rootfs-candidate-composition. Aparelho44/C07/55 hashes/par55/70 intactos; sem instalação/boot/rebuild total. Próximo: plano seletivo de instalação/rollback no128, preservando contador44/seed/SSH/rede/p3 e adaptando preflight ao C07 direto sem marcador C12. Não gravar imagem inteira na raiz viva, resetar contador ou rearmarC12/menu permanente.


**C24r1 instalação seletiva/boot47 APROVADOS:** [migração](phase4-candidate-update.md) aplicou56 arquivos com backup21/rollback/16fixtures, preservando privados/counter/p3 e rede. Boot45→46 voltouC07direto, mas revelou counter644 por umask herdada. Modo foi reparado sem alterar46; r1 corrigiu C07run(umask077+chmod600 tmp) e sua fundação89, com7regressões/13fixtures/backup2. Boot46→47 passou sem intervenção: rootRO0755/counter600/redeSSHfixada/89hashes+payload15/perfil/taint0/erros0. Código legadoC12 inativo retido para rollback, defaultsOff; nenhum flash/partição/kernelDTB/seedreload. Candidato privado recomposto comr1,14fixtures/172loaders/fsck/readback; provas candidate-update-{installed,r1-installed,r1-boot,r1-rootfs}. Próximo: novo boot de uso único da sessãoC22 instalada, preferências+lease, consumo durável e retornoC07, sem rearmarC12/menu permanente.

**C25 boot único/UI/input/lifecycle APROVADOS; áudio pendente:** [C25](phase4-launcher-once.md) instalou nove arquivos/duas pastas com backup2/rollback, fundação96 e defaults off.35 fixtures de política/sessão/arquivo/Kconfig e14 da transação passaram, além de shell BusyBox e recusa manual64. Pedido próprio foi consumido antes doC07:48 abriuC22 instalado/55/70/policy0/lease180 com raízesRO;49 retornouC07 sem UI. Usuário ausente pediu repetição explícita:50 confirmou imagem/D-pad, mas relatou áudio corrompido. Coleta/lease/restauração/checkpoint/daemons/readbackFAT e fallback51 passaram; cinco provas launcher-once-* congeladas e SHA256 conferidos. Host corrigiu regexAWK do coletor e preparação de diretórioRAM ausente (4fixtures), sem novo código nativo por essas correções. [Áudio](phase4-audio-corruption.md) preservou49 avisos PipeWire de falta de buffers, grafo/PCM e métricas dos WAVs; causa ainda não provada, nenhum som extra/ajuste foi disparado. Console51/C07/IP13/rootRO/brilho80/taint0/96hashes/erros0, sem token/ação pendente. Original32/Deck preservados, sem flash/kernelDTB/partições. Usuário ausente novamente: audição e outros testes físicos aguardam aviso de retorno. Próximo: investigar negociação/buffers com uma variável por ensaio; composiçãoC26 permanece pendente e UI permanenteoff.


**C26 áudio limpo/audível APROVADO no52/55/70:** [buffers e nível](phase4-audio-buffers.md) reproduziu chiado alto na C22 normal, separou o problema do WAV e mediu grafo/threads. Force-quantum1024 cessou avisos/chiado; monitor digital de saída (sem microfone) comprovou três WAVs completos bit-exatos. Props confirmaram escala cúbica wpctl55→0,166375; ganho195 trouxe audibilidade limpa em55. S95 aplica/confere quantum1024 antes da UI e perfilv2 define ganho195; dez arquivos seletivos instalados com backup10, fundação96/payload15/perfil21.30checks (6quantum+10perfil+14transação) passaram. Sessão final52/run-0005 SEM overrides host confirmou configuração nativa e usuário confirmou som limpo/audível; zero avisos após navegação, cleanup0/mixer/DRM/cache/brilho80/prefs55/70/daemons/rede/taint0/erros0 restaurados. Provas audio-buffers-correction com SHA256, sem raw/rootfs/blob/segredos; SDKconfig inalterada, sem ELF/reboot/token/kernelDTB/partições ou uso doDeck. Console52 baseC07/IP192.168.15.8/raizRO/sem UI ou ação pendente, original32 preservado. Próximo: composição privada de imagem C25+C26 (S95 atual/perfilv2 antes da fundação, defaults off/sem token). Máximo/faixa acústica/fones/outros painéis/coldboot/energia/suspend/longa duração ainda pendentes. Não repetir baseline ruidosa ou ajuste55/70/USB sem motivo.


**C27 integração e calibração do speaker APROVADAS:** [imagem e volume](phase4-image-volume-calibration.md) integrou C25+C26/coreS95/perfilv3 em ext4 privada512MiB, com fundação96/payload15 idênticos ao alvo nativo. Fsck offline/readback integral/172loadersQEMU/26fixtures e SDK/base intactos passaram; fábricaC07/defaultsoff/contador0/sem token/privados, imagem não gravada ou bootada inteira. Ganho195 tinha máximo baixo;205 limpo/alto, usuário pediu215, aprovado limpo/máximo adequado. Perfil215/certificado instalado por8arquivos com backup7; checks controlador13/transação14/perfil10. Sessão nativa final52/run-0010 sem overrides confirmou0 silencioso e65 limpo/confortável; stop/coleta0 e salvo55/70/restauração/raizRO/rede/96hashes/erros0. Primeira janela45s inconclusiva e rodada com lease expirada/result1 preservadas; prazo corrigido para firstpaint+570 e margem210, rodadas posteriores0. Provas speaker-volume-calibration e rootfs-c25-c26-calibrated/SHA256 conferidos, sem raw/blob/rootfs/segredos. Sem reboot/token/kernelDTB/partições/uso doDeck; original32 preservado. Próximo: boot único C25 com perfil215/S95 atuais e fallbackC07, combinação ainda sem reboot. Imagem inteira/SPL/fones/música/energia/suspend/longa duração seguem pendentes; não repetir calibração aprovada nem rearmarC12/menu permanente.


**C28 boot calibrado/fallback APROVADOS; áudio REPROVADO:** [C28/C29](phase4-calibrated-boot-audio-clock.md) vinculou executor C25 à instalação C27 e composição por contrato/hashes, com23checks host. Primeiro arm recusou antes de RW/token por exigir relatório de fallback em C07 normal; corrigido, registro preservado e trial novo.53→54 abriu UI/D-pad, par55/70 e áudio215/1024 efetivos; usuário confirmou som novamente distorcido. Lease/cleanup/coleta/restauração/daemons/FATreadback passaram;55 voltouC07 sem UI/token/grant. Logs pós-toques46 avisos e PCM≈22050 em vez44100; primeira leitura sem avisos não comprova ausência sustentada. Provas calibrated-launcher-boot-audio-regression e calibrated-launcher-fallback, sem instalar código nativo/perfil novo. C27 físico52 segue histórico, áudio após boot reaberto.

**C29 isolamento silencioso concluído; correção de áudio ainda aberta:** [PCM/clock](phase4-calibrated-boot-audio-clock.md) implementou probe limitado de zeros diretos, lock/namespace/debugfsRO e restore mixer byte-exato. RW S32/S16 default e MMAP S32/S16/RW S32 period512/buffer2048 ficaram≈44,1k (uptime10ms), enquanto C22 normal55 sem toques reproduziu≈22,05k com metadata1024/codec215. Clocks/cache/divisores reportam44,1k, sem medição elétrica; rota direta eraOFF, diferença ainda não isolada. Falha inicial timestampaplay0 e recuperação preservadas; sampler usa uptime e arquiva native-probe.sh sem colisão. C22/players/mounts/RAM encerrados, prefs55/70/rootRO/rede/96hashes/taint0/erros0; console55/C07/IP8 seguro. Prova pcm-clock-isolation/SHA256, nenhum som extra/microfone/reboot/ELF/configuração permanente. Próximo: zeros com mesma rotaSPK_HP/215; depois sink/capture/parâmetros software, sem recalibrar ganho ou promover imagem como corrigida. Original32/Deck preservados.


**C30 IRQ implementado/instalado; audição quente aprovada:** [C30–C32](phase4-irq-rate-negotiation.md) isolou zeros diretos com mesma rotaSPK_HP/215,≈44,1k; política api.alsa.disable-tsched=true em RAM levou period1024/buffer4096/headroom0 e≈44,1k sem buffers. Primeiro ensaio sem observação repetido explicitamente;55/run-0003 confirmou “Ok tudo certo” com alvo ainda ativo. Instalou2públicos/configIRQ+fundação97 com backup2,9wrapper/9candidate/14transação; fonteglobal/privados/contador/prefs55/70/rede/raizRO preservados. Whitelist permite só esse arquivo, vizinho recusado; guarda negada findmnt corrigida. Provas alsa-irq-{ram-preparation,installed}, sem imagem/ELF/kernelDTB/partição.

**C31 boot/fallback passaram; IRQ insuficiente para áudio:** [boot56](phase4-irq-rate-negotiation.md), contrato C30/2deltas/97 e20checks host,55→56/C25→57/C07. IRQ instalado/codec215/q1024/software55 corretos, period1024/buffer4096, zero avisos, mas PCM≈22,05k e usuário confirmou distorção. Cleanup/coleta/prefs/daemons/FATreadback/fallback/rootRO/taint0/erros0 passaram. Provas irq-launcher-boot-audio-regression e irq-launcher-fallback. Não promover warm55 ou ausência de avisos como qualidade apósboot.

**C32 renegociação de taxa negativa e encerrada:** [diagnóstico57](phase4-irq-rate-negotiation.md), C22 normal600 sem overrides, helper limitado48000→0 com PID/starttime e trap. PCM22049,450 em44100 e23999,718 em48000; restaurado cruzou resets de trigger e não admite taxa válida. SWparams efetivos capturados: timestampENABLE/avail_min3072/startLONG_MAX/stop4096/silence0. Force-rate0 restaurado antes de stop; coleta/restauração0 e C07/57/rootRO/97hashes/rede/erros0, sem som extra/microfone/reboot. Prova audio-rate-cycle. Próximo: libasound/zeros com mesmos parâmetros software, um fator por ensaio, antes de nova alteração de startup/kernel. Original32/Deck preservados; imagem C27/96 histórica não contém C30.


**C33–C37 áudio após reboot aprovado no62:** [PCM/startup](phase4-rw-audio-startup.md)
mostrou que IRQ/RW e ausência de avisos não garantem taxa: primeiro menu60
entregou22050.54 para44100; segunda sessão idêntica60 entregou44099.22 e som
limpo. C35 direto/exatosSWparams sofreuEPIPE, foi encerrado/restaurado sem
taxa válida. C36 instalou somente S95+fundação97, com ciclo curto de zeros
viaaplay antes doPipeWire, sem novoELF ou recalibração. Boot62 com política
instalada mediu44101.82/44098.41 antes/depois da navegação e usuário aprovou
imagem/navegação/som limpo.5prime+6quantum+10rate+14transação+20contrato
passaram; lease/coleta62 restauraram mixer/DRM/cache/brilho80/prefs55/70.
Retorno63/C07 aprovado: rootRO/97/rede/taint0/erros0/FAT+p3desmontadas,
sem UI ou token. Nenhuma promoção de UI permanente ouC12.
Original32 e Deck preservados. [C38](phase4-primed-rootfs.md) composto e verificado: ext4ROOTFS512MiB privado,
fundação97 e dez arquivos equivalentes aoC36, fsck/releitura integral,305ELF+
555módulos/172loaders e28fixtures passaram. Provas rootfs-pcm-primed sem imagem
e SHA256SUMS conferidos. SDK/base/imagemC27 preservados; nada gravado no console.
Próximo: qualificar repetibilidade da primeira inicialização em outro boot,
pois existe apenas um boot com o prime aprovado; C12/UI permanente continuamoff.


**C39 repetibilidade e C40 preparação:** [C39](phase4-prime-repeat.md) qualificou
o segundo primeiro-menu após reboot64 com o mesmoC36:44101.07/44100.80frames/s,
imagem/navegação/som limpos confirmados. Lease/coleta/restore64 e retorno65/C07
passaram97/rootRO/taint0/rede/erros0/prefs55/70, sem novo apply ou configuração.
Empacotador forward-only ganhou8checks e recusa do trial original; provas
boot-0064/fallback-0065 preservam62/63 e tiveram SHA256SUMS conferidos.
[C40](phase4-libretro-smoke.md) preparou core MIT semROM/BIOS, RGB565/input/reset/
áudiozero e checker de API. SDK AArch64/-Werror e QEMU com loaderC38 passaram
11frames/8085frames áudio batch+sample, sem ELF enviado ao R35S ou imagem alterada.
Próximo: muxretro nativo em cópia privada do snapshot, dependências offline,
no-content e lifecycle de descendentes antes de ensaio físico. Console65/C07
seguro; original32/Deck preservados, UI permanente/C12 off.


**C41–C43 integração Libretro preparada e testada sem supervisão:**
[muxretro](phase4-muxretro-integration.md) compilado em cópia privada do snapshot
aprovado, rcheevosMIT fixado/hash conferido e libsSDK/C38 preservadas. Patch0007
implementa no-content real e capacidade/cargaNULL;0008 corrige includeDRM.
18casos parser/loader+coreC40 e loader/CLI finalQEMU passaram. NoR35S/65,
C42 executou versão/help/recusas e checker11frames/8085frames áudiozero emRAM,
com prazo/cleanup. Guard da travaRAM700 passou6fixtures. C43 montou preferências
reaisRO+noload, copiou55/70 paraRAM e qualificou S90 com aliases tmpfs e prova
de escrita descartável; originais e mounts globais idênticos.10fixtures e
cleanup/restauração/rootRO/97/rede passaram. Provas host/native-cpu/retro-ram-storage
com SHA256SUMS, semELF/blob/privados. Nada instalado/rebootado; console65/C07.
Usuário ausente autorizou ensaios autônomos; gráfica/input físicos continuam
pendentes. PróximoC44: worker de lifecycle, proteção writerssysfs e término
diagnóstico normal antes de executar a gráfica; C22UI não deve ser simulado.


**C44 gráfica Libretro e direcional APROVADOS:** [sessão nativa](phase4-retro-session.md)
implementou prazo normal no-content1..60s, supervisor com subreaper/grupos/reaping
(10testes reais) e worker isolado C22+C43/sysfsRO (10fixtures), sem S99UI fictício.
Parser18+deadline11/loaderCLI passaram. Falha parcial42 e sinal143 nativos foram
restaurados antes da gráfica. No65, rodada final apresentou2700frames/45s,
PCM44099,15/44100 e usuário confirmou movimento com processo comprovadamente
ativo. Exit0/cleanup0, rootRO/97/rede/PIDs/prefs55/70 e mounts globais preservados;
RAM removida, sem reboot/token/instalação. Prova retro-session-native/SHA256SUMS
conferida; falhaEGL resolvida e observação inicial tardia mantidas separadas.
Áudio do core é zero, sem aprovação acústica de jogo. Original32/Deck intactos.
Próximo: despacho e retorno launcher→muxretro→launcher com coreC40 emRAM,
provas de retorno/erro/sinal antes da observação; core real/conteúdo depois.


**C45 ciclo launcher→muxretro→launcher APROVADO:** [ciclo diagnóstico](phase4-launcher-retro-cycle.md)
implementou despacho fixo no-content e retorno com saída normal/reaping, libmuxmod
privada opt-in e worker RO+RAMprefs com /run/muos e /tmp privados. HookAArch64/QEMU,
binding e14casos passaram; preparo42/sinal143 preservados, falha do core com retorno
42/cleanup0 e ciclo0/cleanup0 requalificados. Primeiro prefixo recusado e regressão
visual do menu (idle nativo omitido) foram registrados/corrigidos. Rodada final
observe.qmmr123o no66: core902frames/15s, menus20→94 e20→183 apresentações,
usuário confirmou funcionamento. Frame estático após exit foi substituído por
página de término com guardas e confirmação física, sem relançar a gráfica.
RootRO/97/rede/PIDs/prefs/mounts preservados, RAM removida, sem reboot/token/
instalação; original32/Deck preservados. Prova launcher-retro-cycle/SHA256SUMS,
semELF/blob/privados. Áudiozero não qualifica som de jogo. C46 preparado como
plano de aplicação diagnóstica selecionada pelo menu nativo, caminho RAM fixo,
recusa/erro/sinal/retorno antes de A/B; nenhum novo teste armado.


**C46 aplicação selecionada nativamente APROVADA:** [seleção](phase4-app-selection.md)
usa A/handle_a do muxapp, um app próprio RAM com caminho/dono/modo/link/inode/
SHA e consumo único, B cancel, core30s e launcher20s. Opções escalares governor/
controller são validadas/consumidas sem sysfs antes do retorno. Corrigidos destino
bundled ausente, LF diferente do writer nativo e flag pendente que abria muxgov;
writer/reader reais noQEMU passaram,13coordenador+6guardas. Duas janelas sem A
levaram a120s para seleção, sem sessão permanente; workerC45 só muda lease150→210,
cleanup comparado literalmente e rollback/B anteriores preservados. Nativeguard
cycle.8sde38we passou6/cleanup0; B aprovado em rheerwqk; A/core/D-pad/retorno
observe.ltxracns no67 aprovados pelo usuário,1801frames/30s e launcher20→84
apresentações, operação0/cleanup0. RootRO/97/rede/prefs/PIDs/mounts preservados,
RAM removida e página finalC46 enviada. Prova native-app-selection/SHA256SUMS,
semELF/blob/privados; nada instalado/rebootado/armado, original32/Deck preservados.
Próximo C47: core real/conteúdo redistribuível, fontes/licenças/ABI/build/API
antes de sessão RAM/RO supervisionada. Sem power/saves/UI permanente por rotina.


**C47 primeiro core real integrado; desempenho aberto:** [NES](phase4-nes-core.md)
compilou FCEUmm GPLv2 fixado e ROM originalMIT, SDK A35 preservado. APIQEMU e
CPU real passaram160frames/RGB565/inputRAM/reset/serialize/áudiozero. Patch0012
permite diagnóstico de conteúdo com prazo/fresh e sem rede de achievements/
netplay;40parser/8guardas/loaderCLI passaram. SeleçãoA/nave/Dpad/retorno aprovados;
cenário corrigido em ROM-only com pixels quantitativos3cores/38nave/160estrelas,
sem recompilar core/host. Final67/cpvhbmpp1544frames/30s,0/cleanup0, rootRO/97/
rede/prefs/mounts preservados e RAM removida. Prova nes-core-content/SHA256SUMS
inclui só ROM própria/fontes/relatórios, semELF/blobs/privados. Addendum registra
≈51,47fps/767underruns: funcional aprovado, velocidade/acústica não. Original32/
Deck intactos, sem reboot/token/instalação. Usuário forneceu ROM privadaGameBoy
em port/roms/gb (ignorada noGit, fora das provas) para futuro coreGB. C48: medir
loop/render/espera/áudio/48→44,1k e preparar coreGB com essa ROM privada.


**C48 desempenho medido e Game Boy preparado:** [medição](phase4-nes-performance.md)
implementou captura automática30s/CSV e medição dos callbacks com workerC46,
rootRO/RAM/sysfsRO/cleanup preservados. Cinco sessões no68 passaram0/cleanup0:
baseline51,40fps, callbacks51,47, espera porsoftware52,47, coreO3/LTO53,57.
API/pixels/input/serialize do core recompilado passaram; nenhuma variante resolve
60fps ou as faltas de áudio, portanto não foi instalada/promovida. Onze guardas
de despacho/CSV passaram, hooksQEMU5callbacksgateantesdoperf_init; fontes/SDK/
provasC47 preservados. GambatteGPLv2 fixado77f2567d, AArch64C++/RGB565/semrede,
compilou e passou loader/metadadosQEMU, sem retro_init/ROM/nativo. ROM privada
GameBoy continua preservada/ignorada, semcópia/execução. Prova C48/SHA256SUMS
semELF/ROM/imagem/privados conferida, consoleC07/68/PCMclosed/RAMremovida,
semreboot/token/instalação. PróximoC49: API e conteúdo privadoGB/RAM, taxa e
áudio real antes de teste físico; desempenhoNES continua aberto e requer separar
CPU/espera/apresentação, sem clocks/USB/calibração/reboots por rotina.


**C49 Game Boy com ROM privada APROVADO:** [conteúdoGB](phase4-gb-content.md)
reutilizou GambatteGPLv2/AArch64 e hostC47 sem rebuild/instalação. APIQEMU e
CPU real615frames/160x144RGB565/áudio nãozero/input/reset/serializeRAM passaram;
8guardas de launcher e11de sessão usam fixtures sem ROM comercial. GráficaRAM
2691/45≈59,8fps e observação2690/45≈59,78, ambas zero faltas de áudio; usuário
aprovou imagem/Start/D-pad/som. ALSA48000mediu48000,49frames/s, sem retocar
215/q1024/IRQ/volume55. Retorno técnico launcher20→84 e0/cleanup0, rootRO/97/
prefs/rede/mounts preservados e RAM removida. Prova gameboy-private-content/
SHA256SUMS semROM/ELF/imagens/PCM/saves/segredos, com hashROM privado redigido.
Original32/Deck preservados; semreboot/token/instalação. PróximoC50: saídaFn+Start
com distinção de término voluntário versus prazo/falha, retorno e restauração,
sem Power/saves duráveis. NES/desempenhoC48 continua aberto; GB não o resolve.


**C50 saída Fn+Start e retorno APROVADOS:** [hotkeyGB](phase4-gb-hotkey-exit.md)
implementou --diagnostic-hotkey-exit restrito a conteúdo/prazo, procedência
hotkey versus internal/remote e classificação com frames reais/deadline/falha.
Autosave/timeline/flush periódicos off só nos settingsRAM. Host privado novo,
coreROM/worker/UI/SDK/refs intactos;40parsers antigos+12novos+26policyQEMU e
9fixtures passaram. Fallback45s+retorno2691frames/59,8fps/zero faltas/cleanup0;
A/jogo/FnStart nativo encerrou547frames/expired0/reasonhotkey e retornou ao
launcher, confirmado pelo usuário. Zero faltas/cleanup0/rootRO/97/prefs/infra/
mounts preservados e RAM removida; nada instalado/rebootado/armado. Prova
gameboy-hotkey-exit/SHA256SUMS semELF/ROM/frames/PCM/saves/segredos conferida,
C49 preservado. PróximoC51: save/load manual só emRAM pela UI nativa, conferir
Fn+R2/Fn+L2/suporte/caminhos antes do físico; persistência/Power fora do escopo.
NES/desempenho e longa duração/novo boot continuam pendentes.


**C51 quicksave/quickload em RAM APROVADOS:** [estado GB](phase4-gb-state.md).
Host/core/UI/ROMC50/C49 intactos; integração dos hotkeys existentes Fn+R2 e
Fn+L2 com inspeção PKST/CRC/manifesto/assinatura PNG no namespace privado.
18 fixtures A35/QEMU e5cenários de retorno/falha passaram. Nativo boot68:
um save e dois loads,26861bytes válidos; usuário “Tudo certo!”, Fn+Start e
retorno normais,2453frames/expired0/operação0/cleanup0. Dados RAM removidos,
rootRO/97/prefs/mounts/infra preservados, páginaC51. Semreboot/instalação/Deck/
original32. Prova gameboy-ram-state semestado/ROM/PNG/PCM/ELF/segredos.
CSV contou8callbacks/5eventos/3471frames ausentes(0,106s), semtimestamps:
funcionalidade aprovada, continuidade de áudio durante interação ainda aberta.
PróximoC52: auditar e preparar persistência limitada a saves com backup e
recuperação, sem unir Power/suspend/flash. Nada durável habilitado neste passo.


**C52 store versionado e laboratório ext4 APROVADOS:** [armazenamento de saves](phase4-save-store.md).
Implementado muos-save-store MIT com gerações imutáveis, bundle de três folhas,
CRC/identidade, HEAD atômico, fsync/flock, recover explícito e limite32 sem GC.
34fixtures A35/QEMU passaram. No boot68, imagem ext4 temporária emRAM passou
commit A/B, remountRO/exportaçãoB, recusaRW/fonteext4, corrupçãoB preservada,
recoverA/remountRO/exportaçãoA e fsckoffline. Auditou p3 real somenteRO/noload:
prefs55/70 intactas, pickles/save existentes e port-saves-v1 ausente. RootRO/97,
infra/mounts preservados; loop/cápsulas/ELFs/imagemRAM removidos. Prova
save-store-laboratory semblobs/estados/ROM/segredos. Nenhum jogo/áudio/input,
reboot/instalação ou save comercial no cartão. PróximoC53: integrar cópia
seletiva do store ao C51 e validar duas sessões supervisionadas salvar/carregar;
backup/identidade/guard/sync antes de habilitar gravação durável limitada.


**C53 persistência seletiva entre sessões APROVADA:** [integração GB](phase4-gb-persistence.md).
32fixtures A35/QEMU; bootstrap exclusivo/fsync/NOREPLACE preserva paiMUOS0755 e
cria árvore própria0700, guardC20/C22, sem alterar root/boot. StoreC52 inicializado
vazio, depois save.hi07rjg_ publicou geração1 após Fn+R2/saídaFnStart/inspetor.
RAM/runtime encerrados e removidos. load.i2to6dts exportou p3RO→RAM e restaurou
posição exata porFnL2, confirmado pelo usuário, retornando ao launcherFnStart.
Store byte-idêntico na segunda sessão; operação0/cleanup0/rootRO/97/prefs55/70/
infra/mounts preservados, p3desmontado. Geração1 comercial retida apenas no128,
semcoleta deestado/PNG/manifesto/ROM/ELF/PCM/segredos. Prova
 gameboy-selective-persistence conferida comidentidade/hashROM redigidos.
Save1216frames/zero underruns; load1214frames/4callbacks/1971frames ausentes
(~0,060s), semtimestamps deeventos. Não atribuir causalidade ou dividir por45.
Host/core/UI/worker C50/C49/C46 e C36áudio byte-idênticos, seminstalação/reboot/
token/flash/Deck/original32. PróximoC54: novo C07 controlado e verificar a mesma
geração porroleload, com recibo debootanterior explícito; nada armado.


**C54 restauração após novo boot APROVADA:** [snapshot entreboots](phase4-gb-after-boot.md).
Retomada encontrouC07/boot69 já ligado; snapshotC53 vinha do68. Adaptador novo
vincula recibos explícitos/imutáveis e identidade/assets sem afrouxarC53; gate
seed/verify/loadonly, seminicializador.26fixtures passaram. Nativo906frames/
hotkey/expired0/26861bytesválidos, FnL2 restaurou posição do68 e FnStart voltou
aomenu, usuário “Tudo certo”. Store byte-idêntico ao68 e antes/depois, p3RO/
cleanup0/rootRO/97/prefs/infra/mounts preservados; RAMremovida, geração1retida
somente no128. Prova gameboy-after-boot comidentidade/hashROM/bootUUID redigidos,
semestado/ROM/PNG/ELF/PCM/segredos; C53/C52 intactos. Nenhum reboot foi pedido
peloagente; método do shutdown não observado. CSV4callbacks/1932frames ausentes
(~0,059s), semcausa localizada; core_hzrecente58,9971 não é throughputtotal.
PróximoC55: pacoteBuildroot opt-in do storegenérico/defaultsoff/zlib/MIT, sem
conteúdo privado e semwriter/autostart automático. NadaC55armado.


**C55 pacote Buildroot opt-in APROVADO:** [receita do store](phase4-save-store-package.md).
MUOS_SAVE_STORE AArch64/defaultoff/zlib/MIT, semserviço/writer/identidade/dados
privados. Kconfig/rsync/legal-info reais, i386 confirmado/seleção recusada,
fontes legais exatasC/LICENSE/contrato, macros reais com SDK e loader A35/QEMU.
ELF byte-idêntico ao C52;34fixtures/labext4 reutilizados. ÁrvoreprivadaC38 recebe
somente4arquivos/3diretórios; inventárioanterior inteiro preservado, fundação97/
payload15/perfil21/defaultsoff/contador0/manifests válidos. Nenhuma imagem nova,
fullrebuild ou novo boot do pacote. Lint check-package indisponível por módulo
magic ausente no container; host seminstalações. Console69 rootRO/PCMclosed/
p3desmontado/infra idêntica aoC54, pacote ausente; semreboot/token/menu/writes.
Prova save-store-package sófontes/metadados; C52/C54/SDK intactos, original32/
Deck preservados. PróximoC56: gerar e verificar imagem ext4 privada offline,
readback/fsck/contratoboot, seminstalar/rearmar/flashar ou habilitarwriter.


**C56 imagem ext4 privada APROVADA OFFLINE:** [imagem com store](phase4-save-store-image.md).
C38 +4arquivos/3diretórios C55,512MiB/ROOTFS; fsck-fn0/releitura integral3330itens
iguais aoC55, nenhum itemC38 alterado, donos/modos dosnovos+raiz conferidos.
Fundação97/payload15/perfil21/manifesto3/gateC07/contador0/defaultsoff válidos.
306ELFsuserspace+555módulosAArch64, ABI4.4.0/ext4features iguais à base; novoCLI
loaderA35/QEMU/status64 passou. Demais172loadersC38/34fixturesC52 reutilizados
para bytes iguais, semreplay. SHA07a18d14ef54c91b7e463a016155165deff33296fdf833b8dbca51ff38780ef6
em build/phase4/save-store-image/image.nlnmgzzb/images/rootfs.ext4. Prova
save-store-image sófontes/recibos, semrootfs/ELF/dadosprivados. SemfullBuildroot,
recompilação/bootnativo/SSH/cartões/Deck; últimoestadoC55console69 não foi relido.
PróximoC57: plano de implantação seletiva dos4arquivos no128, inventário/backup/
rollback/guardas, semautostart/writerautomático nem sobrescrever raizcomimagem.
Primeiro conferir estado real; testes nativos apenasRAM sintética/rootROfinal,
sem repetirjogos/USB/áudio. Original32preservado; nadaC57armado.


**C57 pacote instalado seletivamente APROVADO:** [implantação do store](phase4-save-store-installed.md).
Quatro arquivos C55/hash4/modes/link1 e3diretórios novos no128, zero originais
substituídos; ausência-backup+pacoterecuperação fsynced nohost, rollbackexato.
26fixtures passaram, inclusive dirnameBusyBox'//' corrigindo pré-inspeção
inicial semRW/apply; cápsula falha removida. Final boot69inspect0/apply0,
CLIinstalado init/status0/recover3 emRAMsintética; fundação97/rootRO/taint0/
PCMclosed/p3desmontado/infra/mounts/fingerprintprivado preservados. SemnovoELF,
serviço/token/menu/reboot; RAMremovida e4arquivos passivos retidos. Prova
save-store-installed sófontes/recibos, semtar/ELF/estados/ROM/segredos.
Original32/Deck intactos. PróximoC58: diagnóstico usaCLIinstalado com manifesto/
hash pinned, runtime e estadosRAM/p3RO porpadrão, commit sóexplícito; fixtures
de despacho/recusa antesde futura sessão supervisionada. Preservar C53/C54,
não repetirprepare/save porrotina; nadadespachado/armado. BootimagemC56 e
novobootdopacote, frontendpermanente/Power/suspend/GC/SRAM/áudio/NES separados.


**C58 backend usa CLI instalado APROVADO SEM GUI:** [despacho instalado](phase4-installed-store-backend.md).
Dispatcherstatus/export loadonly fixa CLI C57/hash4/modes/links/pais/rootRO;
recusa cópiaELF na cápsula, opsmutáveis/argumentos/identidade/role incorretos.
Backend derivadoC53 remove prepare/commit/RW, C53/C54originais intactos.
34fixtures comstat/dirnameBusyBoxA35/QEMU; primeiroprobenativo stat-f não
compilado corrigido parafindmnt/cleanup0. Final native.ewspqvb0 boot69 usa
CLIinstalado em2status+1export, p3RO/noload namespaceprivada/runtimeRAM;
PKST/CRC/manifesto/PNG/26861bytes válidos, storeHEAD1/0/2 byte-idêntico C54 e
antes/depois. SemROM/core/UI/áudio/novo save/reboot/instalação, sóinspetorELF
inalterado transferido. RootRO97/prefs55/70/infra/mounts preservados; p3off/
RAMremovida, pacoteC57 passivo. Prova installed-store-backend sófontes/recibos
sanitizados, semidentidade/ELF/ROM/estados/hashbundles/segredos; original32/Deck
intactos. PróximoC59: sessãoGB comCLIinstalado, restauraçãoFnL2/saídaFnStart
supervisionadas semnovo save, guardasboot/recibos/lifecycle mantidas; nadaarmado.


**C59 Game Boy com CLI instalado APROVADO:** [sessão instalada](phase4-gb-installed-session.md).
Retomada já emboot70; vínculo novo C54/C58origem69→70 e UUIDdiferente, sem
alterar guardasC53/C54 ou pedir reboot.29checks deproveniência/delta passaram;
34fixturesC58/lifecycleC45 reutilizados. Native load.uzlnx4ac623frames/hotkey/
expired0/operação0/cleanup0, FnL2 restaurou posição e FnStart voltouao menu,
usuário “Tudo certo”. CLIinstalado em2status+1export, nenhumELFstore enviado;
PKST/CRC/manifesto/PNG/26861bytes válidos, HEAD1/0/2 e store idênticos C58/C54.
RootRO97/taint0/PCMclosed/prefs55/70/mixer/DRM/volume/WirePlumber/infra/mounts
preservados, p3off/RAMremovida/telafinalC59. PacoteC57 aprovado no70 após69
observado, semcontrole de shutdown. CSV4callbacks/1539frames ausentes sem
causa; core_hzrecente59,9401 não é throughputtotal. Prova gameboy-installed-store
sófontes/recibossanitizados, semROM/ELF/estados/IDs/segredos, original32/Deck
intactos. PróximoC60proposto: receitaBuildroot opt-in do hostmuxretro, revisar
origem/licença/ABI/deps, core/ROM/saves excluídos e autostartOFF; nadaarmado.


**C60 receita muxretro APROVADA OFFLINE:** [pacote do host](phase4-muxretro-package.md).
Opt-in/defaultoff com SDKprivado explícito e quatro bibliotecas C38/hash;
provider frontend completo ainda pendente. Fontes frontend1.195 coincidem
C50, SITE1.300textos/9licenças, rcheevosMIT fixado; Kconfig/rsync/legal-info
reais e recusa semSDK/i386/SDKausente/adulterado antesdocompilador passaram.
Compilação limpa pelas macros/SDK, ELF AArch64/PIE/RELRO/NOW/RUNPATHcorreto,
loader eager A35/QEMU/version/help válidos. NovoELF8d519958 difere C50; sem
transferir aprovação física ou qualificar reprodutibilidade binária/GPU.
Warnings upstream/EGL preservados. ComposiçãoC56 recebe13arquivos/13dirs,
preserva3.330itens/fundação97/payload15/perfil21/manifests/C07/contador0/defaultsoff.
Semcore/ROM/save/serviço/writer/autostart/libsplataforma novos, semimagem/
fullrebuild/instalação/SSH/reboot. Prova muxretro-package sófontes/licenças/
metadados; C50/C59/C56/SDK intactos, consoleúltimoverificadoC59/70 não relido,
original32/Deck fora do fluxo. PróximoC61: qualificar novoELF emRAM comguardas/
recibos próprios e leitura doestado real, sessãoGBsupervisionada/loadonly/
FnL2/FnStart semnovo save, antesdeinstalação. Provider completo separado;
nadaarmado. Compositoreshistóricos podem recusar menu novo porlinhagem;
adaptadorC60 não altera suasguardas nem provas.


**C61 host C60 APROVADO EM RAM:** [ensaio do pacote](phase4-muxretro-package-session.md).
Adaptador separado derivaC59exato, mantém vínculos históricos assets68/recibos69/
execução70 e exige contador+UUID C59; sóentão substitui host pelo payload C60.
52checks de recusa/vínculo/delta + loader eager A35/QEMU com libmuxmodC46
passaram. ELF8d519958 passou version/help nativos e sessãoGB load.upr3y148,
1197frames/hotkey/expired0/op0/cleanup0. Usuário “tudo certo” paraimagem/entrada/
som/FnL2/FnStart/retorno; novohost qualificado nesse runtimeRAM comoverrideC46,
semreusar aprovação antiga do ELF. CLIinstalado2status/1export, PKST/CRC/
manifesto/PNG/26861bytes válidos, HEAD1/0/2/store byte-idênticos C59/C58/C54.
RootRO0755/fundação97/taint0/PCMclosed/p3off/prefs55/70/infra/mounts preservados,
RAMremovida/páginaC61/hostausentenorootfs. Semnovo save/instalação/reboot,
original32/Deck fora dofluxo. CSV4underrun/1932frames ausentes; Hzrecente59,9401
não é FPS absoluto, áudiocontínuo/novo deadline interno nãoqualificados.
Prova muxretro-package-session sófontes/recibossanitizados, C59/C60/C58/SDK
intactos. PróximoC62: plano seletivo13arquivos cominventário/backup/rollback/
guardas e ativação manual, explicitando dependênciaC46 antesde aplicar.
Provider completo/bootimagem/novohostapósreboot/frontendpermanente separados;
nadaC62armado.


**C62 muxretro INSTALADO PASSIVAMENTE:** [implantação seletiva](phase4-muxretro-installed.md).
13arquivos/13dirs C60 no128, zeroexistentes substituídos, ELF8d519958 exato.
Native inspect0/apply0, hashes/modos/nlink1/dirs e105pré-requisitos preservados
(fundação97+4libs+4C57); CLI instalada version/help eager passou comlibs padrão.
61fixtures novas cobrem13mkdir/13stage/13publish, rollback/recusas/BusyBox//,
pai compartilhado e retenção de conteúdo/vizinhos/temporários inesperados.
Plano/backup deausência/tar fsynced em muxretro-install/install.67io22z3;
zero originais copiados, nãoimagemintegral. Lock/cardguards/noclobber/hardlink/
sync/RO/fingerprintprivadoRAM; trap selaRO, recuperaçãoarquivada seletiva.
Final C07/70/IP14/rootRO0755/PCMclosed/taint0/p3off/UIoff/infra/mounts iguais,
cápsularemovida/hostpassivo. SemGUI/save/reboot/token/libsnovas, C61físico
nãorepetido; C46RAMéoverride dosmenus, hostapp herdalibs padrão. Original32/
Deck fora dofluxo; store/prefs semmontagemC62, últimoestadoC61retido. Prova
muxretro-installed sófontes/recibos/plano, C60/C61/C57/SDK intactos. Não
repetir prepare/apply/rollback ou saúdeC61queexigeausência. PróximoC63:
diagnóstico usa hostinstalado comguardas/manifesto/recibos/semELFfallback,
seleçãoC46RAM/CLIstoreloadonly e sessãoGB supervisionada semnovo save.
Nadaarmado; provider/bootimagem/frontendpermanente/novohostapósreboot separados.


**C63 diagnóstico com HOST INSTALADO APROVADO:** [sessão instalada](phase4-installed-host-session.md).
Delta exatoC61 + guardfixo13hashes/modos/pais/manifesto/roleload/rootRO/tmpfs,
semELFhost/store nacápsula/fallback/argsextras. Vínculos C61/C62 exigemmesmo
bootinteiro70/UUID e assets, semalterarguardasantigas.104checks(45binding+
59dispatcher) passaram semhardware/ROMcomercial; dirnameBusyBoxA35 incluído.
Primeirajanela expirousemseleção, cleanup0/rootRO/RAMremovida; coletor herdado
acusou logverify ausente apóscleanup, semaprovação. Repetição solicitadapelo
usuário e semextensãotempo: load.szcr_1jo954frames/hotkey/expired0/op0/cleanup0,
execobservado /opt/muos/frontend/muxretro/sha8d519958, FnL2/saída/retorno/
imagem/som confirmados “Tudo certo”. CLIstoreinstalado2status/1export,
PKST/CRC/manifesto/PNG/26861bytes/storegen1HEAD1/0/2 byte-idênticos C61/C58/C54.
RootRO0755/97/105prereqs/13arquivos/taint0/PCMclosed/p3off/prefs55/70/infra/
mounts preservados, RAMremovida/páginaC63. Seminstalação/save/reboot/token,
original32/Deck fora dofluxo; helpers/caller aindaRAM, seleçãoC46dosmenus.
CSV5underruns/2091frames ausentes semcausa; áudiocontínuo/deadline nãoaprovados.
Prova installed-host-session sófontes/recibossanitizados+timeout, C60/C61/C62/
SDK intactos. PróximoC64: imagemext4privada offline comC56+C60/C62, inventário/
readback/fsck/C07/manifests/contador0, semcaller/ROM/core/save/autostart,
semflash/SSH/reboot/fullrebuild e reutilizando checks para bytesiguais.
Provider/frontendpermanente/novobootdoHost/bootimagem separados; nadaarmado.


**C64 imagem privada com MUXRETRO APROVADA OFFLINE:** [rootfs integrado](phase4-muxretro-image.md).
Cópia C56 +13arquivos/13dirs C60/C62,512MiB/ROOTFS; imagem SHA671a738792d5a6b718d698f8386488d14216c8f539541f2b6160e1bbc98a62a6
em muxretro-image/image.n_uthilw/images/rootfs.ext4. Fsck-fn0, releitura integral
3.356itens iguais à composiçãoC60,3.330anteriores C56 preservados. Root0755/
uidgid0 e26inodes novos/modos/13nlink1 conferidos; fundação97/payload15/perfil21/
manifests/linksSDK/C07/contador0/defaultsoff válidos. Estático307userspace+
555módulosAArch64/ABI4.4.0/featuresext4 iguaisC56. Loaders172C38+1storeC56+
1hostC60 e nativoC63 reutilizados para mesmos bytes/deps; semreplay/compilação/
fullrebuild/SSH/mount/flash/boot. CallerC63/C46diagnóstico/core/ROM/save/
preferências privados fora; imagem privada, provider/licenças ainda pendentes.
Prova muxretro-image37hashes sófontes/recibos; C56/C60/C62/C63/SDK intactos.
IPnovo192.168.15.10 informado pelo usuário, nãoverificado; últimoestado vivo
C63/boot70/IP14, seminferir contadoratual. Cartões128/original32/Deck fora dofluxo.
PróximoC65: bibliotecasfrontend como integraçãoBuildroot offline, origem/licenças/
patches/deps/ABI, fundação separada deC46; ELFnovo requer qualificação antesde
substituir. Bootimagem/frontendpermanente/novobootdoHost separados; nadaarmado.


**C65 provider de BIBLIOTECAS FRONTEND APROVADO OFFLINE:** [receita e limites](phase4-frontend-libs.md).
Segunda árvore externa port/buildroot-frontend/MUOS_R35S_FRONTEND, opção
MUOS_FRONTEND_LIBS defaultoff/AArch64, sem alterar receitas/Config.in históricos
ou selecionar SDK/C60/serviços/boot. Fontes fixadas frontend5e8635b3 e mojibake0.3.6,
patches0003/0006, 1.274textos/1.195frontend exatos/11licenças. Kconfig/rsync/
legal-info reais, recusa i386, archive texto exato; build/install macros comSDK
existente, semfullrebuild. Target17arquivos/4libs+11licenças+proveniência+manifesto;
staging isolado4libs, semheadersSDK. ABI/NEEDED/exports/tamanhos/GLIBC/RELRO/NOW/
ORIGIN e RTLD_NOW4libs+CLI C60 QEMU/A35 passaram. Stage build.84o1r4aj;
libui639c1df8/libmuxcom2913dbf7 diferentes e aindanãoqualificadas nativamente;
libmuxmodbfd909c6/libpluto99377c31 idênticas àfundação, varianteC46 separada.
Dois builds limpos com4ELFs iguais entre si; nãoqualifica firmware completo.
Primeiroprobe isoladoUI falhou mux_tick; carregargrupo porlibmuxmod corrigiu
sóoprobe, semstubs. Prova frontend-libs96hashes sófontes/licenças/recibos;
C60/C62/C63/C64/SDK/imagem671a7387 preservados. SemSSH/dispositivo/cartão/Deck,
C60aindacomsuaSDK; IP10informado/nãoverificado, última saúdeC63boot70/IP14.
PróximoC66: qualificar novaslibs emRAM, mantendoC46/hostinstalado eguardas;
primeiroverificar estado/boot, semafrouxarvínculosC63. Consumidorprovider depois,
semreescreverC60. Bootimagem/frontendpermanente/Power/suspend separados; nadaarmado.


**C66 provider FRONTEND APROVADO EM RAM:** [sessão nativa](phase4-frontend-libs-session.md).
Inspeção constatou boot71/UUIDnovo/IP10; C63 segue vinculado ao70 semedição.
Prefixo offline C63 valida históricoC53–C63; novaobservação/pins71/UUID/infra/
recibosC63-C65 autorizam callerC66 separado. 66checksnovos(27binding/delta/syntax+
39guardRAM), lifecycleC45/104C63 reutilizados. Menus C65ui/common/pluto+C46mod;
jogo4C65 viaLDfixo ehostC62instalado, semELFhost/store nacápsula. Guard7folhas/
hashes/modes700/dirs700/tmpfs/env, guardinstalado13arquivos preservado. Probe4libs+
CLI eager nativos e maps/exe dos3processos confirmaram novaslibs carregadas.
Stage load.o2agwm0q:1732frames/hotkey/expired0/op0/cleanup0, FnL2/FnStart/retorno/
imagem/som confirmados “Tudo certo!”. CLIstore2status/1export/PKSTCRC/26861bytes,
storeHEAD1/0/2 byte-exatoC63/C61/C58/C54; semnovosave/reboot/instalação. RootRO0755/
97/105prereqs/13instalados/PCMclosed/taint0/p3off/UIoff/prefs55/70/infra/mounts
preservados, RAMremovida/páginaC66. CSV5underrun/1737frames ausentes semtimestamps,
Hzrecente59,9401 nãoFPSabsoluto/áudiocontínuo. Prova frontend-libs-session28hashes
sófontes/recibossanitizados, C63/C62/C65/C64/SDK/imagem671a7387 intactos.
Original32/Deck fora dofluxo. Hostinstalado/provider qualificados na sessão manual
apósbootnovo observado; origemreboot/startupautomático nãoqualificados.
PróximoC67: consumidorBuildroot dependente providerC65, novaárvore/receita preserva
C60; staging/link/composição offline, semreinstalar/repetirGB porrotina. Novobyte
host requer qualificação. ROMGB basta; outrosconteúdos só paraoutroscores.
Bootimagem/frontendpermanente/Power/suspend separados; nadaarmado.


**C67 MUXRETRO CONSOME PROVIDER BUILDROOT, APROVADO OFFLINE:** [receita e composição](phase4-muxretro-provider.md).
Árvore nova port/buildroot-muxretro/MUOS_R35S_MUXRETRO preserva Config.in/receitas
C60/C65 fixados. Opção defaultoff/AArch64 seleciona MUOS_FRONTEND_LIBS, grafo
real depende muos-frontend-libs, recusa hostantigo/i386, semexigirSDKprivado. FontesC60
reusadas com manifesto/prova,1302textos/982compartilhadosC65/10licenças;
legal-info textoexato. ProviderC65/C66 não recompilado, macro staging real em
cópia doSDK,5recusas missing/corrupt antesCC. Primeira tentativa linkfalhou
por scripts glibc absolutos fora dosysroot; helper --sysroot explícito corrigiu,
novostage build.f9a1ac69 completo, semeditarSDK/GPU/refs. NovoELFcd67ce605cfa406f6084c7348ebf27d475b73340edd981c1343f07b00a995e9d
AArch64PIE/ABI4.4.0/RELRO/NOW/RUNPATHfixo; eagerCLI+LD_DEBUG4libs QEMU/A35 passaram.
Diferentehost8d519958, semtransferir aprovação físicaC66 ou instalar/executar.
Target31arquivos; composição C56+27files/29dirs=3386itens/0remoções, só4libs
anteriores mudam(2hashes/4modos755→644),3326intactos. Fundação97/payload15/
perfil21/store/manifests/C07/contador0/defaultsoff válidos, imagemC64 intacta.
Prova muxretro-provider102hashes sófontes/licenças/recibos, C56/C60/C64/C65/C66/
SDK preservados; semSSH/console/cartões/Deck. ÚltimovivoC66/71/IP10, nãoatualizado.
PróximoC68: hostC67 emRAM comproviderqualificado/C46/loadonly, guardexato sem
substituirC62/fallback e estado/bootUUID conferidos; nenhuma janela armada.
Futuraimagem precisa loadersafetados pois2libs mudaram, semreuso indiscriminado
C38. Fullrebuild/bootimagem/frontendpermanente/Power/suspend separados.


**C68 hostC67 APROVADO EM RAM:** [qualificação](phase4-muxretro-provider-session.md).
NovoELFcd67ce60 emcapsule/host/muxretro, guardfixo semfallback e13instalados
preservados; providerC65/C46/runtime/lifecycle C66 iguais. 28checks(11binding+
17dispatcher), obs71/UUIDC66 exatos; outrobootrecusado. load.8ef49rho903frames/
hotkey/expired0/op0/cleanup0, exeRAM/maps4libs/menu3+C46, física “Tudo certo”
paraimagem/entrada/som/FnL2/FnStart/retorno. CLIstore2status/1export/PKSTCRC/
26861bytes/inventáriosC66-C54 iguais. RootRO0755/97/105/13/PCMclosed/taint0/
p3off/UIoff/prefs55/70/infra/mounts preservados/RAMremovida/páginaC68.
CSV5underrun/1637ausentes/Hzrecente58,8813 seminferirFPS/áudiocontínuo.
Prova muxretro-provider-session28hashes sófontes/recibossanitizados;
semreboot/instalação/novoSave/cartãooriginal/Deck. C65/C66/C67/SDK/C64 intactos.
Usuário autorizou continuidade sempausas entremarcos. PróximoC69: imagemoffline
comcomposiçãoC67/fsck/readback/owner/modo/C07/manifests e refresh seletivo dos
loaders afetados; não reexecutar demais semmudança bytes/deps. Semflash/boot.


**C69 IMAGEM PROVIDER/CONSUMIDOR OFFLINE CONCLUÍDA:** [recibos e limites](phase4-provider-image.md).
Novaext4512MiB SHA b03842ff7ce2a8ddc22948c3bd8002cef832222dd54c3b58e79ae54b587b3e6c,
composiçãoC67/3386itens/fsck0/C07/contador0/manifests/owner/modos passaram.
31folhas regulares link1;27files+29dirs novos/4libs alteradas(2hashes/4modos).
Loaders4afetados refrescados,170reusados sócom fechamento de dependências
byte-idêntico C38/C56. Prova provider-image51hashes sempayload; baseC56/C64/
SDK preservados. SemSSH/cartão/boot; componentes aprovadosRAM emC68 não
qualificamboot daimagem. PróximoC70: conjunto privado de cartão completo com
bootchain/kernel/DTB/layout aprovados; semflash/provisionamento/novoSave.


**C70 IMAGEM DE CARTÃO PRIVADA CONCLUÍDA OFFLINE:** [layout e limites](phase4-card-image.md).
640MiB SHA f82f9ddd56b29765a4d852c6ef7dce0a0a6678915a4426d3c706155b77293671,
MBR/FAT/rootfsC69/bootchainB01 integrados. Releitura5regiões+gapszero+6folhasFAT/
partições extraídas/fsckFAT/gzip passou; fsckC69 reusado porhash idêntico.
27guardas de arquivo regular; semflash/SSH/boot/Deck. FactoryC07/contador0/
defaultsoff semcredenciais/seed/hostkeys/p3/ROM/saves. Provisionamento/boot
supervisionado pendentes. Prova card-image sófontes/recibos; payload privado
nãoredistribuível. PróximoC71 prepara migração seletiva providerC65+hostC67
combackup público/rollback testados, semgravarimagemC70 no cartãoativo.


**C71 TRANSAÇÃO PROVIDER/CONSUMIDOR OFFLINE APROVADA:** [modelo e rollback](phase4-provider-upgrade.md).
Plano5substituições/26adições/12metadadosobsoletos/29dirsnovos/13antigos;
backup17originais públicos e101prereqs preservados. 140fixtures passaram,
incluindo falha emcada etapa decriação/staging/publicação/remoção e guardas/
rollback/preservação deconteúdo estranho. Prova provider-upgrade sófontes/
planos/recibos, sempayload. Nenhum RW/escrita/reboot/flash. Leiturasaúde
C72preparo confirmouIP10/71/UUIDC68/rootRO/97/C62quiet. PróximoC72: vínculo
exato, checksadapternativo e atualização seletiva, semgravarimagemC70.


**C72 PROVIDER E HOST INSTALADOS:** [transação nativa](phase4-provider-upgrade-native.md).
Cartão128/71/IP10 recebeu5substituições+26adições/12remoções metadados;
29dirsnovos/13antigosretirados. Hostcd67ce60 e4libsC65 agora instalados,
31hashes/modos/link1/manifests válidos. 18fixtures adapternativo passaram;
apply0/rootRO/97/101preservados/privados/infra/mounts iguais/PCMclosed/p3off/
UIoff/RAMremovida/páginaC72. Dlopen4+hostCLI passaram após corrigir caller
posicionalC65 noresumidor, erro original arquivado semredispatch/rollback.
Prova provider-upgrade-native sófontes/recibos sanitizados; backup17públicos
independentehostinstall.otw0lflu. SemGUI/novoSave/reboot/token/serviço/flash/
original32/Deck. C73próximo usa guarda31instalados/vínculo novo/C46RAM,
load-only/mesmosbytes qualificados; não executar guardahistóricaC68 noestado novo.


**C73 FECHADO / C74 REBOOT DO USUÁRIO APROVADO:** [sessão instalada](phase4-installed-provider-session.md),
[retorno no72](phase4-installed-provider-return.md). C73/71 confirmou física e
1193frames/hotkey/maps/store byte-idêntico; fechamento interrompido usa recibos
já coletados, sem repetir jogo ou simular saúde atual. C74/72/IP18 vinculou
novoUUID e verificou31folhas/101prereqs/ABI4+host/rootRO/quiet/infra/mounts,
semGUI/áudio/p3/reboot/escrita persistente. RAM removida. Texto piscando sumiu
após reboot do usuário; causa não comprovada. C75 offline iniciado: receita
Buildroot do Gambatte qualificado, sem ROM/instalação/autostart. Metadados de
licença passam a registrar GPLv2/GPLv3/MIT por arquivo, REDISTRIBUTE=NO.


**C75 CORE GAMBATTE EM RECEITA BUILDROOT, OFFLINE APROVADO:** [implementação](phase4-gambatte-package.md).
Novo external buildroot-libretro/defaultoff/AArch64/C++, archive C49 fixado.
Kconfig/extract/legal-info reais e recusa i386 passaram; macros com SDK
existente produziram ELF SHA3e0940da byte-idêntico ao usado no C73. API/loader/
exports/RELRO/NOW passaram sem ROM; não repetir física para esses mesmosbytes.
Target9arquivos/8dirs no caminho nativo /opt/muos/share/core; composição3403
preserva3386itens C69/C07/contador0/defaultsoff. Sem instalar/gerarimagem/
acessarconsole/Deck/original32. Prova gambatte-package sófontes/recibos.
Licenças porarquivo GPLv2/GPLv3/MIT registradas, revisão conjunta pendente e
REDISTRIBUTE=NO. Primeira fixture arquitetural corrigida com --keep-case;
stagefinal build.tgnlr06f aprovado. PróximoC76: implantação seletiva com
backup deausência/rollback/guardas próprios; caller instalado em etapa própria.


**C76 CORE GAMBATTE INSTALADO:** [instalação e recuperação](phase4-gambatte-installed.md).
Cartão128/boot72/IP18 recebeu9folhas0644+8dirs,0substituições; core3e0940da
no caminho nativo /opt/muos/share/core, mesmosbytes C49/C73/C75. 50fixtures
passaram; inspect/apply0/manifesto/132preservados e probe loader/API1/metadata
nativos aprovados sem retro_init/ROM/GUI/áudio. RootRO0755/PCMclosed/p3off/
UIoff/taint0/privados/infra/mounts preservados, RAMremovida. Backupausência
independentehost install.ucdyhb4b, semrollback nativo/perdaelétrica. Prova
gambatte-installed sófontes/recibos; original32/Deck/SDK/imagens intactos.
Licença conjunta pendente/private-only mantidos. PróximoC77: caller fixo
pelo core instalado, guarda9folhas adicional e mapas, sem cópia coreRAM;
vínculo novo/fixtures antes física. Nenhum novo teste ou token armado.


**C77 CALLER COM CORE INSTALADO APROVADO:** [sessão e diferenças](phase4-installed-core-session.md).
Boot72/IP18, host/providerC72 e coreC76 fixos, sem transferir coreELF paraRAM.
47casos offline e dispatcher40nativo passaram; mapas menuC46→jogo instalado→
menuC46 aprovados. Física confirmou imagem/input/áudio/Fn+L2/Fn+Start/retorno,
1161frames/hotkey/expired0/operação0/cleanup0. SnapshotC63 idêntico via
exportTMPFS no namespace nativo gambatte;0renomeações/escritas no cartão.
RootRO0755/97/132preservados/PCMclosed/p3off/UIoff/taint0/infra/mounts iguais,
RAMremovida/páginaC77. Usuário relatou abertura mais lenta (sem medição) e
paleta verde: esta explicada pelo coredef nativo colorization=internal ao
reconhecer gambatte. CSV59,8802Hz/3underruns/1499frames ausentes agregados,
sem qualificar áudio contínuo. Prova installed-core-session sófontes/recibos;
sem novoSave/reboot/token/autostart/flash/original32/Deck. PróximoC78 proposto:
imagem ext4 offline com pacoteC75/manifesto/fsck/readback; boot e caller
permanente separados, licença conjunta pendente/private-only preservados.


**C78 IMAGEM EXT4 COM GAMBATTE APROVADA OFFLINE:** [imagem e verificações](phase4-gambatte-image.md).
Novaext4512MiB SHAa09edf63..., composiçãoC75/core3e0940da no caminho nativo.
9folhas+8dirs,3386itens C69 preservados/3403total, zero substituições.
Fsck0/releitura integral/18inodes owner+modos/9folhas link1/manifestos/C07/
contador0/defaultsoff passaram.308ELFs userspace+555módulos/ABI/features
preservados.174loaders C69 reusados por hashes transitivos idênticos; probe
MIT novo confirmou dlopen eager/API1/metadata no core extraído viaQEMU/A35,
sem retro_init/ROM. Hashes C69/C70 eSDK preservados. Prova gambatte-image
sófontes/recibos, sempayload. SemSSH/cartão/Deck/física/novoSave/reboot/flash.
Revisão conjunta de licença pendente/private-only mantidos. PróximoC79:
novaimagem privada de cartão usando raizC78 e layout/bootchainC70; verificar
regiões/FAT/readback, semgravação/provisionamento/boot automático.


**C79 IMAGEM COMPLETA COM GAMBATTE APROVADA OFFLINE:** [composição e limites](phase4-gambatte-card-image.md).
Raw640MiB SHAe9deed97.../gzip64.988.906bytes, raizC78 a09edf63... comcore
3e0940da integrada ao bootchain/kernel/DTB/layoutC70. MBR/5regiões/gapszero,
6folhasFAT/readback/duaspartições/hash/fsckFAT0/gzip passaram. SóPROBE.TXT
mudou no FAT; bootchain3regiões eImage/DTB mantidos. Fsck/inventário3403/
ABI/loader/probeC78 reusados após rootextraída byte-idêntica;27fixturesC70
reusadas por fontes e recibos iguais. Raw/gzipC70/ext4C78/SDK preservados.
Prova gambatte-card-image sófontes/recibos; semSSH/cartão/Deck/flash/boot/
provisionamento/novoSave. FactoryC07/contador0/defaultsoff semprivados/ROM/
userdata/resize/callerC77; licenças conjuntas pendentes/private-only mantidos.
PróximoC80: preparação de provisionamento/recuperação/backup antes de boot
supervisionado, preservando MBR/p3/saves/estado privado atuais do128GB;
rawfactory não é migração que preserve esses dados.


**C80 PLANO DE MIGRAÇÃO P2 E SURVEY APROVADOS:** [contrato e recuperação](phase4-root-migration.md).
IP18/boot72/rootRO/quiet/40instalados/132preservados/97/infra/MBR iguais;
três partições reais e prefixo16MiB compatívelC79 excetop3. Leitura apenas de
metadata/hash de6arquivos, sem exportar seed/key/config. Planner e gates
puros limitam futura escrita a p2/128MiB+512MiB, preservando MBR/p1/p3 e
recusando rawfactory global.84casos sintéticos passaram; nenhum backend,
backupoffline, provisionamento ou operação de escrita/boot foram executados.
Seed0400/auth0644/auxiliar.pub0600 tratados por allowlist específica. Backup
fresco640MiB+hostindependente+prefs/saves p3 exigidos; candidata mantém seed
offline/contador atual. Rollback automático e restore byte-exato pós tentativa
deboot inelegíveis, por replayseed/recuocontador. Prova root-migration redigida,
semprivados. PróximoC81: helperoffline backup-only/testes e desenho de recuperação
pósboot antes de propor implantaçãoC79. Original32/Deck/SDK/imagens intactos.


**C81 HELPER DE BACKUP PREPARADO OFFLINE:** [contrato e evidências](phase4-offline-backup.md).
Pedido explícito do usuário limitou a etapa a offline: sem SSH/console/Deck,
troca de cartão ou backup real. Helper local one-shot somente backup, sem
servidor/writer/format/restore; núcleo de cópia, coletor host e pacote privado
vinculado ao C80/boot72.72casos passaram, incluindo extração debugfs/fsck de
ext4 sintética16MiB e tar lógico em container sem dispositivos; host-copy e
bootstrap têm fixtures sintéticas. Guardas CID/aliases/todos namespaces/
swap/holders/fsck0/ro+noload/hash/fsync e inventários incluídos. Prova
offline-backup sem plano privado/UUID live/hashes privados/payloads; SDK
baseline igual. Não qualifica execução completa no Deck nem backup do cartão.
Próximo: ao retomar hardware, validar boot e renovar survey/pacote se mudou;
agendar backup test128+segunda cópia e implementar recuperação pósboot antes
de qualquer candidata provisionada/escrita/bootC79. Original32 preservado.


**C82 BACKUP OFFLINE + CÓPIA INDEPENDENTE APROVADOS:** [resultado e limites](phase4-backup-native.md).
DeckJupiter/IP13/test128, mesmo boot72. Primeira recusa causada por root0777:
SteamOS automount aplica chmod777 se deck não pode escrever no mount. Auditor
da parcial confirmou os outros pais/identidade e permitiu validação privada
local sem reler cartão. Política explícita para backup pinada por hashes,
padrão0755 ainda estrito;86casos+17transporte+11auditor passaram. Backup640MiB,
FAT/raiz exatas, seis arquivos privados e nove prefs/saves aprovados; fsck das
três partições0, cartão desmontado e snapshot removido. Cópia host hash/tar/
fsync independente; esparsa com bytes preservados para SSD. Prova backup-native
sem planos/privados/payloads. Sem seedload/keygen/provisionamento/writer/reboot.
P2/p3 raiz0777 preservadas no backup, reparo obrigatório antes de qualquerboot.
PróximoC83: correção guardada somente de metadata root:root0755 e prevenção
de automount, sem reutilizar formatterC20 ou generalizar escrita p3 pelo C80;
depois recuperação pósboot monotônica antes de migraçãoC79. Manter test128
no Deck, original32 fora do fluxo; SDK/imagens preservados.


**C83 MODOS DAS RAÍZES REPARADOS:** [resultado e limites](phase4-root-permissions.md).
Inspeção nativa/cápsula independente seguida de aplicação guardada: dois setores
512, somente seis bytes de modos/checksum, root:root0755 em p2/p3. Prefixo640MiB
pós-hash previsto, superblocks/descritores intactos, fsck0 e nove prefs/saves
iguais; sem hash integral118GiB p3. 44casos com ext4/checksums reais e falhas
sem retry/rollback. Cópias C82 e cápsulas C83 preservadas Deck/host; prova
root-permissions redigida, ancestrais intactos. Cartão desmontado/kernelRO
nos quatro aliases; regra temporária /run pinada ao CID impede automount,
/usr original intacto. Sem seedload/keygen/firmware/provisionamento/reboot.
Original32/SDK/imagens preservados. PróximoC84: recuperação pósboot com seed
fresco/sem crédito e contador monotônico antes da migraçãoC79; manter test128
no Deck e proteções ativas. C83 não fornece restore ou writer genérico.


**C84 CONTRATO DE RECUPERAÇÃO PÓSBOOT APROVADO OFFLINE:** [resultado e limites](phase4-root-recovery.md).
Registro exclusivo de possível boot antes da entrega, fsync/readback pinado,
sem cancelamento por falta de SSH. Captura offline nova deve trazer fsck0,
contador e identidade estável; recuperação reserva max confirmado+1 e substitui
ambos seeds antigos por seed.no-credit256 fresco, getrandom não bloqueante sem
fallback/retry/crédito/carga. 85casos passaram, incluindo ext4 sintéticas reais,
fsck0/árvore pública/rede iguais, backup intacto e política de entropia real com
stubs; a fonte coincide com C79 extraída. Preparo C82/C83 vinculado/contador72/
seis privados conferidos; sem seed/fence/imagem de recuperação real. Prova
root-recovery redigida. Deck confirmado desmontado/kernelRO/regra C83;
original32/SDK/ancestrais intactos. PróximoC85: coletor pósboot e compositor de
imagem regular de produção; depois backend p2-only/fence antes de migraçãoC79.
Contrato/payload não são recuperação física pronta; manter cartão no Deck.


**C85 COLETOR DE SNAPSHOT/COMPOSITOR REGULAR APROVADOS:** [contrato e limites](phase4-recovery-image.md).
Núcleo de produção sem mounts/init/blocos, CLI512MiB e36casos sintéticos32MiB:
recuperação com contador reservado/seed.no-credit0400, árvore pública/rede/
attrs/históricos preservados, fontes intactas e falhas de IO sem conclusão.
Reference C82 real512MiB passou fsck0/3.669entradas/seis privados/nove marcadores
consumidos; hash fonte igual e privados substituíveis sem EAs externos. Consumo
histórico validado/preservado, .once ativo recusado. EAs externos em privados
substituídos recusados antes de clonar por limite observado do debugfs, sem
reparo genérico. Ressalva fixtureC84root777 coberta agora por inode explícito;
provas antigas imutáveis, C83físico independente. Sem seed/fence/captura pósboot
real/recuperação real/SSH/cartão/gravação/reboot; original32/SDK/imagens intactos.
17imagens sintéticas antigas descartadas após logs,274.661.376bytes liberados.
Prova recovery-image só fontes/casos/resumos. PróximoC86: captura física RO
com contexto derivado e depois backend p2-only/fence antes da migraçãoC79.
Manter cartão no Deck com proteçãoC83; C79 ainda não liberada para gravar/bootar.


**C86 CAPTURA FÍSICA DE REFERÊNCIA APROVADA:** [contrato e execução](phase4-physical-capture.md).
Helper local sudo reference/postboot, sem servidor/writer/restore/seed/boot.
48casos de integração/RO/recibos/bootstrap passaram, protocolo real sobre
ext4 sintética com guardas físicas stubadas. Referência real no DeckJupiter/IP13
aprovou p2 de512MiB, fsck0, contador72, seis privados e3.669entradas; releituras
p2/MBR/prefixo16MiB iguais e cópia host hash/fsync/scannerC85/árvore integral
independente aprovados. Cartão desmontado, todos aliasesRO/regraC83 intactos,
snapshot root removido; original32/SDK/imagens/backupC82 preservados. SóSETRO1,
sem limpar proteções; sem p3/FAT. Referência não emite contexto pósboot. Modo
postboot implementado exige fenceC84 anterior e deriva contexto do IO; ainda
sem validação física desse modo. Prova physical-capture sanitizada; snapshots
512MiB privados Deck/host não substituem backupC82prefixo+userdata. PróximoC87:
backend p2-only testado offline e transição explícita de proteções/fence, depois
ciclo físico pósboot/recuperação antes de candidataC79. Manter cartão no Deck.


**C87 PARCIAL — NÚCLEO P2 PREPARADO:** [contrato](phase4-p2-write-core.md).
Usuário pediu encerrar com3% de limite. Primitivo de intervalo fixo p2, intenção
antes de escrever, short-write sem retry, hashes/fsync/readback e proteção em
finally;16casos virtuais passaram. Sem controller/entrypoint físico ou SETRO0,
sem deploy/payload/seed/fence/boot. Prova p2-write-core sanitizada. Retomar
controller, validação de fonte/backups/journal e transição RO/fence antes de
implantar. C87 incompleto e C79 não liberada; cartão protegido no Deck.

**C87–C90 ATUALIZADOS — BOOT DE REFERÊNCIA 73 CONFERIDO:**
[C87](phase4-p2-controller.md) qualificou o controlador em loop real,
incluindo escrita512MiB, leitura fria e falha curta sem retry. C90 qualificou
o claim O_RDWR e a transição RO no MMC real, sem payload, com três leituras
integrais da p2 iguais. Provas p2-controller/card-readiness congeladas.
[C88](phase4-initial-image.md) provisionou e transferiu uma candidata regular
privada, sem mídia; contador72 ficou desatualizado após o novo boot.
[C89](phase4-p2-recovery.md) tem75casos offline aprovados e prova
p2-recovery-prepared; ainda sem execução física do recuperador.

Registro C84 da instalação C76 atual foi selado antes da entrega ao R35S.
Boot73 conferido por SSH: arquivos instalados, root0755/RO, p3 desmontada,
PCM fechado, nenhuma sessão/.once ativo e RNG inicializado. Desligamento
normal solicitado; usuário ausente, troca de volta ao Deck adiada.
Retomar por captura C86 postboot com esse registro existente, composição C85,
recuperação C89 p2-only e cópia independente do próximo fence, depois boot
de qualificação. C79 continua sem liberação de gravação/boot. Estado e
caminhos privados no [checkpoint](phase4-resume-checkpoint.md).

**C86 PÓS-BOOT APROVADO; C89 NATIVO EM EXECUÇÃO:** captura real após boot73
passou fsck0, cópia host/hash/fsync e scan C85 independente com árvores e
observações iguais. C85 compôs recuperação regular com contador74 e seed
fresco sem crédito, identidade/árvore preservadas. Pacote C89 conferido e
helper iniciado no Deck; conclusão física ainda pendente. Observador sem sudo
com17casos acompanha somente esta tentativa e chama coleta/publicação uma vez
após término, sem iniciar/interromper/repetir writer. Cinco leituras integrais
do complemento tornam a execução demorada. Manter mídia offline até coleta
do próximo fence. [Execução e limites](phase4-p2-recovery-native.md).

**05/11/2026 — RECUPERAÇÃO C89 E BOOT75 APROVADOS:** helper e observador
concluíram escrita somente p2, releitura fria, preservação integral do
complemento e coleta independente do próximo fence. Prova p2-recovery-native
conferida antes de mover mídia. Primeiro boot esperado75 passou em verificação
SSH somente leitura: C07/rede/arquivos/identidade, root0755/RO, p3/FAT off,
PCM fechado e seed sem crédito consumido com RNG pronto/nova rotação.
[Resultado e limites](phase4-p2-recovery-boot.md). Usuário encerrou por hoje;
Deck ainda necessário, backups/ferramentas preservados. Próximo: atualizar
estado privado e preparar migração inicial C79; C88estado72 não pode ser usada.

**C92 COMPOSITOR INICIAL APROVADO OFFLINE:** [resultado e limites](phase4-initial-migration.md).
FactoryC79+captura pós-handoff vinculada produzem arquivo regular com árvore
pública nova, identidade/EAs/históricos preservados, seed.no-credit256 fresco
e contador reservado. C88/C85/C84 reutilizados sem alterações; intermediário
consumido sem outra cópia512MiB. 25casos em ext4 sintéticos reais passaram,
incluindo estado72 antigo, RNG/falhas parciais/estágios repetidos e symlink.
Prova initial-migration congelada, sem imagem de produção512MiB, rede/cartão,
deploy/fence/boot ou backend físico novo. Manter cartão no R35S por enquanto.
Próximo: preparador/controlador finito e validação de captura atualizada antes
de pedir retorno ao Deck. C79 ainda não liberada para escrita/boot.

**C93 PREPARADOR/CALLBACK INICIAL APROVADOS OFFLINE:**
[Vínculos e limites](phase4-initial-preparer.md). Preparador exige fence C89,
primeiro boot qualificado e captura nova, revalida backups host por descritor
e reutiliza factory privada pinada à C79; claim recusa composição repetida.
Callback deriva elegibilidade C92 de scans reais por FD antes de futuro unlock.
30casos passaram em ext4 sintéticos; auditorias reais conferiram12artefatos
host/factory512MiB e recusa de captura73 antes de gerar seed/estágio/container.
Prova initial-preparer congelada. Sem main positivo completo, nova candidata,
device/deploy/fence/boot. Próximo C94: entrada privilegiada finita, pacote,
recebimento/coletor e testes. Manter cartão no R35S até backend preparado;
C79 não liberada, C89/boot75 preservados sem repetir ensaios físicos.


**C94 ENTRADA INICIAL PREPARADA OFFLINE:** [contrato e limites](phase4-p2-initial.md).
Writer finito migrate separado de recover C89, fábrica C79 pinada, lineage de
recuperação/boot e recaptura física, três scans por FD, controller C87/C90 só p2,
fence e coleta independentes. Preparador, receivers, coletor, observador e prova
nativa implementados. 84casos offline passaram (43entrada/41transporte);
transação com ext4 reais sintéticos32MiB e adaptadores físicos substituídos.
Prova p2-initial-prepared congelada. Sem nova candidata512MiB/deploy/escrita/boot;
mains positivos completos ainda não exercitados. Recusa real de captura73 antes
de SSH/RNG/estágio. R35S respondeu no novoIP192.168.15.16, boot76/CID correto,
root0755/RO, p3 desmontada, PCM fechado, sem UI/.once. Próximo: desligamento
normal, retorno supervisionado ao Deck, captura atualizada com fence existente74,
C93 compose e C94 migração/coleta. Original32 e recuperação C89/boot75 intactos.

Guardas C76/boot76 passaram e desligamento normal foi solicitado com SSHexit0;
aguarda confirmação de console apagado, cartão no Deck e novo IP do leitor.
Nenhuma escrita/deploy C94; preparador permanece bloqueado por captura73 antiga.


**C95/C96 AUTOMOUNT NOVO RESOLVIDO:** [proteção/captura](phase4-card-rearm.md),
[reparo atual](phase4-root-repair-current.md). Deck sem guarda em/run montou
p2/p3RW após transferência; ambas raízes0777 no boot76. Usuário desmontou.
C95 restaurou guarda/RO1 e capturou preimage atual independente (27casos).
C96 derivou dois setores atuais e reparou6bytes/1024bytes gravados, com journal,
controles C87 verificados, sem retry, fsck0/root0755/prefix/SB/GDT/userdata
preservados (29casos). Coletas e provas nativas separadas congeladas; C83 antigo
inalterado. Cartão no Deck192.168.15.13, RO/guard/unmounted. Preparando captura
C86postboot com fence C89existente74, depois C93/C94. Sem migração C79 ainda.

**C94 MIGRAÇÃO INICIAL NATIVA APROVADA,05/11/2026:** captura C86 atual76,
composição C93 candidata77 e pacote C94 vinculados. Escrita512MiB só p2,
releitura fria e cinco passagens integrais de preservação do complemento
MBR/p1/p3 aprovadas. Novo fence copiado/verificado independentemente no host,
RO/guard/unmounted/semhelpers conferidos. Prova `p2-initial-native` congelada.
Observador interrompido antes da coleta; retomada manual após inspeção, sem
retry do writer. Test128 liberado para primeiro boot C79; original32 guardado.

**C97 COLETOR PREPARADO:** [contrato](phase4-initial-boot.md), 25casos offline
e caminho positivo de lineage com imagens/recibos reais passaram. Guarda141
arquivos comparada à candidata C79 por hash e metadados. Coleta SSH somente
leitura verificará boot78/identidade/entropy NC sem crédito/RO/idle. Primeiro
boot e main nativo ainda pendentes. C98 duas passagens é apenas rascunho sem
testes/adaptador físico; não altera C94 nem autoriza outra escrita.

**C97 PRIMEIRO BOOT C79 APROVADO:** usuário transferiu test128 ao R35S e
informou192.168.15.8. Boot78 passou coleta SSH somente leitura:141arquivos por
hash/metadados, identidade4 preservada, root0755/ext4RO, p1/p3 desmontadas,
PCM fechado, sem UI/BT/.once. NC2048bits consumido sem crédito, readiness e
seed creditável novo256bytes, hashes antigos ausentes. Timeout inicial anterior
ao SSH foi preservado; repetição somente leitura no mesmo boot passou.
Main positivo C97 exercitado; prova `initial-boot-native` com14arquivos e
5ancestrais verificados, sem dados privados. C94/candidata77 não podem ser
repetidos após boot. Próximo: validar fluxo instalado sobre a árvore C79;
nenhum novo teste de áudio/jogo/controles nesta coleta.

**C99 FLUXO INSTALADO SOBRE C79 APROVADO:** [resultado e limites](phase4-c79-session.md).
Executor C77 reutilizado em namespace de evidências próprio, vinculado a C94/
C97 e ao boot78/UUID qualificado; guardas141arquivos/metadados. A migração total
revelou /etc/asound.conf e /mnt/mmc ausentes: duas tentativas pararam antes de
GUI, foram auditadas/limpas e preservadas. Delta novo prepara visões /etc e /mnt
em RAM privada, sem rootRW/regravação, com38casos e ensaio nativo reais de bind/
restore, além de47casos C77 reutilizados. Sessão corrigida1001frames/hotkey0,
mapas instalados, restore sem save, retorno ao menu e confirmação física de
imagem/direcional/áudio aprovados. Snapshot byte-idêntico, rootRO0755/PCMclosed/
p3off/UIoff/taint0, preferências/mixer/DRM/mountinfo/infraestrutura restaurados.
Próximo: corrigir layout da imagem/instalação em incremento pequeno antes de
autostart; não repetir C94 nem C99 aprovado. C98 otimização raw continua rascunho.

**C100 LAYOUT OFFLINE APROVADO:** [contrato e limites](phase4-c79-layout.md).
Fábrica C79 original pinada e preservada; arquivo regular derivado acrescenta
asound.conf644/444bytes do template público existente e /mnt/mmc755 vazio.
29casos em ext4 reais32MiB e composição completa512MiB passaram, com fsck0,
releitura3406entradas, comparação exata do inventário e UUID/features/geometria
preservados. Sem novo raw640/gzip, provisionamento, seed, instalação ou boot.
Próximo: delta aditivo finito444bytes+diretório com recuperação/guardas, sem
migração integral p2. C99 aprovado não foi repetido; autostart permanece separado.

**C101 LIMPEZA MANUAL CONFIRMADA:** [registro](phase4-deck-cleanup-current.md).
Backup host12artefatos/fence/provas reconferidos antes da limpeza. Helper passou
14casos mas execução local falhou; usuário preferiu instruções diretas e confirmou
remoção de arquivos/regra temporária e da chave de tarefa. Sem auditoria SSH
posterior, aprovação nativa do helper ou medição de bytes liberados. Deck fora
do fluxo atual; backups/ferramentas locais e original32 preservados.

**C102 LAYOUT INSTALADO APROVADO:** [instalador e recibos](phase4-c79-layout-install.md).
Delta C100 aplicado ao R35S no mesmo boot78: /etc/asound.conf444bytes0644 e
/mnt/mmc0755 vazio, sem substituir arquivos ou regravar p2. 35casos de
transação/recuperação passaram em container isolado; remounts físicos são
callbacks na fixture. Execução nativa0, raizRO0755,141arquivos/metadados e
template preservados, fingerprint privado/infraestrutura/mountinfo idênticos,
PCMclosed/p1p3off e cápsula removida. Coleta retomada após janela de espera,
sem redespacho. Nenhum reboot/jogo/seed/counter/save/token/autostart novo.
Deck não acessado. Próximo: caller usando layout instalado, sem o contorno
RAM C99 que exige ausência dos caminhos; fontes/provas C77/C99 preservadas.

**C103 FLUXO COM LAYOUT INSTALADO APROVADO:** [sessão e limites](phase4-native-layout-session.md).
Worker original C77 reutilizado no mesmo boot78, sem helper/visões completas
de /etc e /mnt do C99. 26casos novos de vínculo C102/layout passaram;47casos
C77 aprovados reutilizados por integridade, sem repetição. Menu→GB→menu com
imagem/direcional/áudio/restore Fn+L2/saída Fn+Start confirmados pelo usuário.
1160frames, hotkey0/expired0; mapas instalados, snapshot byte-idêntico, nenhum
save. Layout C102 preservado, rootRO0755/PCMclosed/p1p3off/UIoff/taint0,
hardware/preferências/infraestrutura/mountinfo restaurados e cápsula removida.
Prova própria native-layout-session; C77/C99/C100/C102 históricos intactos.
Próximo: qualificar este fluxo em novo boot explicitamente observado, antes
de ampliar frontend/autostart; sem nova migração/seed ou acesso ao Deck.

**C104 FLUXO APÓS REBOOT APROVADO:** [transição e recibos](phase4-reboot-layout-session.md).
Pedido único normal por PID1, claim fsync antes da chamada; retorno78→79 no
mesmo IP, UUID novo e quatro arquivos estáveis de identidade conferidos.
Guarda regenerada com141arquivos/metadados e layout C102, sem alterar vínculos
C103 ou ler seed pelo observador. 22casos novos passaram; 26C103/47C77
reutilizados por integridade, sem reexecução. Menu→GB→menu/restauração/saída/
som limpo confirmados fisicamente,1084frames hotkey0/expired0; snapshot igual,
nenhum save. Layout/rootRO0755/PCMclosed/p1p3off/UIoff/taint0, hardware/
preferências/infraestrutura/montagens restaurados, cápsula removida e prova
reboot-layout-session congelada. Não qualifica boot frio ou longa duração.
Próximo: preparar caller como componente instalado manual, mantendo autostart
separado e sem repetir este reboot, C94 ou qualquer imagem provisionada antiga.

**C105 CALLER MANUAL INSTALADO,07/11/2026:** [contrato e recibos](phase4-manual-caller.md).
17arquivos/1diretório/60.276bytes, sem substituições, imagem integral ou autostart.
43casos caller/transação +4grupos de vínculo/12variantes negativas; nova guarda
conserva inventário e c25_ready. Boot80 com USB recuperado permaneceu falhado;
um reboot normal único trouxe81, observado com identidade atual sem reescrever
C104. Instalação/check142dependências/stage10scripts/recusas passaram; rootRO,
fingerprint/infra/mountinfo preservados e RAM removida. Próximo: sessão gráfica
pelo entrypoint instalado, sem repetir a instalação ou pedir Deck.

**RETENÇÃO E GIT LOCAL:** [limpeza e política](storage-retention.md),404.812
arquivos descartados,11,8GiB físicos recuperados; build41→18GiB. Cinco marcos
de firmware com exceções concretas, código/docs versionados e builds menores
por componente. SDKs/provas/backups/refs preservados; ROM e dados privados
fora do índice Git. Não criar uma rootfs inteira por edição de script.

**C106 FLUXO PELO CALLER INSTALADO APROVADO,07/11/2026:**
[Integração e recibos](phase4-installed-caller-session.md), boot81 existente.
Host não envia dez scripts; stage/run C105 e worker instalado confirmados por
marcador/PID/starttime/cmdline e mapas.17casos novos;43C105+4grupos reutilizados.
Menu→GB→menu, imagem/input/som/restauração/saída confirmados,1255frames e
snapshot preservado. RootRO, hardware/preferências/infra/mountinfo restaurados,
RAM removida, sem imagem/reboot/instalação persistente. Abertura mais lenta
reportada, ainda sem medição de latência. Próximo: preparar assets/cápsula no
aparelho, com plano da origem da ROM/dados; autostart/navegador geral separados.
Cenário de dongle adiado pelo usuário. Mais515MiB físicos recuperados em
fixtures/pacotes antigos, mantendo relatórios e dependências C104/C105/C106.

**C107–C111 PREPARAÇÃO LOCAL,07/11/2026:**
[Contrato inicial](phase4-local-preparation.md), [modos reais](phase4-local-preparation-v2.md)
e [callback final](phase4-local-preparation-v3.md). Três revisões aditivas de
seis arquivos,31.689bytes ao todo, sem substituir C105 ou gerar imagens.
42→43→44casos de preparo/transação: modo0644 das bibliotecas e callback
real de tmpfs corrigem lacunas encontradas antes da conferência física.
Instalações/check/recusa vazia/limpeza aprovadas no boot81, rootRO e
fingerprint/infra/mountinfo preservados. C108/C110 não qualificados para preparo
gráfico; a revisão C111 é a entrada explícita da integração C109.

**C109 INTEGRAÇÃO APROVADA:** [fluxo](phase4-prepared-capsule-session.md).
22checks locais, guarda178 e identidade real core/ROM contra C63 passaram.
Cápsula recebe5inputs em vez de12 uploads; sete bibliotecas e dez scripts
vêm da instalação, metadados/identidade são gerados no aparelho. Preparo
positivo/ABI, menu→GB→menu/imagem/input/som/Fn+L2/Fn+Start aprovados numa única
conferência física,1284frames, snapshot preservado. Native/fechamento0, RAM
removida/raizRO, hardware/preferências/infra/mountinfo restaurados. Prova própria
prepared-capsule-session congelada.
Sem reboot/Deck/save novo; ROM continua RAM. Watcher mediu8,42s entre observações seleção→primeiro frame e1373,11ms de
startup interno; sem timestamp físico do botão ou causa atribuída. Retenção atéC111
conferida, dry-run sem novos descartes; firmware permanece limitado a5marcos.

Próximo lote: residência dos quatro assets públicos restantes, instalação e
integração antes do próximo teste físico; manter a ROM como input RAM, sem
montar/gravar p3 por suposição. Qualificar novo boot com observador próprio se
necessário, mantendo claims consumidos. Autostart/navegador geral separados.

**C112–C114 APROVADOS,07/11/2026:** [assets](phase4-resident-assets.md),
[ROM interna](phase4-internal-rom.md) e [preparo automático](phase4-resident-preparation.md).
Usuário ampliou escopo para ROM interna; cartão128 permanece no console.
Boot82 observado com identidade estável, sem pedido de reboot.13arquivos/
1.871.877bytes aditivos em raiz, quatro assets qualificados e helper MIT fsync.
ROM64KiB importada uma vez na p3, shelf próprio700/arquivos600, com backup lógico
independente43entradas/88.064bytes e snapshot/preferências anteriores intactos.
52+21checks locais, instalação/importação/releitura0, rootRO/p3off/RAM removida.
Preparo residente sem uploads e com leitura da ROMlocal proibida passou;11assets,
10scripts/identidade/manifestos/CLI/ABI conferidos sem iniciar UI/core/input/áudio.
Não houve imagem integral, formatação, repartição ou acesso ao Deck.

**C115 PRONTO, FÍSICO PENDENTE:** [integração](phase4-resident-session.md).
16checks adicionais e observação nativa boot82/191hashes passaram; histórico
admite ROMp3 por recibo nativo em três pontos, preservando outros bindings.
Loop de uploads com mapa vazio efetivamente não lê/envia assets/ROM. Usuário
ausente: não executar rodada gráfica nem publicar confirmação sintética.
Próximo passo é UMA rodada supervisionada A/Start/direcional/Fn+L2/Fn+Start,
com análise/fechamento/prova próprios depois. Backup/claims C112/C113 preservados.
Trace atéC115 e retenção de cinco marcos aprovados, zero novos descartes.

**C116 APROVADO,09/11/2026:** [contexto pós-boot](phase4-resident-boot-session.md)
para boot83/IP13, sem repetir instalações ou importação.21checks offline,
guard191 e observação nova passaram; histórico C112–C115 preservado. Rodada
inicial expirou sem A, com cleanup0. Repetição solicitada sem ampliar prazos:
1051frames, restore/saída por hotkeys, snapshot exato, imagem/input/som/retorno
confirmados. Análise/fechamento/prova `resident-boot-session` concluídos;
raizRO/PCMclosed/p3off/UIoff/RAM removida/infra/mountinfo preservados.
Demora relatada: seleção→primeiro frame observado7,37s, startup interno1,339s,
carga conteúdo27,95ms. Amostragem nominal1s sem timestamp físico ou custo de
cada guarda; não atribuir causa nem declarar ganho comparativo. Áudio registrou
4underruns/1556frames ausentes, sem distorção relatada; longa duração pendente.
Próximo: perfilar fases da abertura e preparar otimização preservando guardas
e fontes/provas históricas. Sem imagem nova, reboot, instalação ou uso do Deck.

**C117 APROVADO,09/11/2026:** [perfil automático](phase4-launch-profile.md),
boot83,17checks offline e11recibos nativos0. Sem pedir botões: três repetições
dos checks originais, host40+provider7 mediana3000ms, provider isolado610ms,
hashes conteúdo+cópiaRAM160ms. Host inclui provider; caches aquecidos e uptime
centesimal, sem controle de frequência ou abertura gráfica medida. Dupla
validação completa check→launch é candidata a otimização, não causa exclusiva
demonstrada. Zero uploads,11assets/10scripts/manifestos preservados, run.once
ausente, sem GUI/core/input/áudio/reboot ou escrita persistente. Infra/mountinfo
idênticos, raizRO/p3off/PCMclosed/UIoff e RAM removida. Prova launch-profile
sanitizada; C116 físico não repetido. Próximo: verificação por lote com testes
de equivalência negativos e benchmark sem UI, mantendo todos os checks.

**C118 APROVADO em check,09/11/2026:** [lote](phase4-batch-validation.md),
51checks locais/36paridades reais de aceitação-recusa e12recibos nativos0 no83.
Um stat de folhas/ancestrais e um sha256sum por lote mantêm as exigências dos
loops anteriores; headers/tipos/modos/owners/links/hash preservados. Protótipo
refusa launch. Três rodadas alternadas: host2990→1130ms (62,2% menor mediana),
provider600→560ms. Não é abertura real nem promessa de ganho físico. Somente
dois programas shell em RAM; originais/runtimeinputs/infra/mountinfo intactos,
rootRO/PCMclosed/UIoff/p1p3off/RAM removida, sem escrita persistente/reboot/Deck.
Prova batch-validation congelada. Próximo: contrato caller/preparador versionado
para integrar o host otimizado sem invalidar o conjunto C105; manter caminho
anterior e só depois qualificar launch e fluxo gráfico. Ganho pequeno do
provider favorece considerar sua preservação. Sem nova imagem integral.

**C119 APROVADO em adoção/check,09/11/2026:** [caller versionado](phase4-batch-caller.md),
39checks offline/32casos shell reais e15recibos nativos0 no83. Seis arquivos
somenteRAM/28.743bytes adotam host em lote, com provider/worker originais.
Metadados antigos byte-idênticos, backup/novo stage ligado ao boot e reserva
atômica de run.once antigo antes da troca; tentativa parcial não pode repetir,
CLI run recusada. Host adotado+provider original1190ms numa amostra; não é
abertura gráfica medida. Pacote instalado C105/guard191/assets preservados,
infra/mountinfo iguais, RAM removida e raizRO/PCMclosed/UIoff/p1p3off. Prova
batch-caller; sem imagem, instalação, save, reboot ou Deck. Primeiro ensaio
preservado antes de correção somente do publicador para incluir fontes shell;
segundo ensaio vincula a fonte final. Próximo: versão explícita para run e
vínculos gráficos no stage novo, mantendo load-only e medindo abertura real.

**C120 contrato/adoção APROVADOS; gráfico pendente,09/11/2026:**
[Run limitado](phase4-batch-run.md),47checks offline/43casos shell reais e
15etapas nativas0 no83. Novo contrato observe cria run.once antes do exec;
argv original subreaper240s/namespace/worker/filho210s/jogo45s, provider intacto.
Fixture executou o despacho, erro74 e recusas sem retry. Executor gráfico
adaptado para novo stage/witness/host, ainda sem execução aprovada. Usuário
pediu somente automáticos: no console apenas check/adopt/staged, run inválido
e integridade; run válido não chamado. Hostcheck1190ms numa amostra, sem
abertura real medida. Infra/mountinfo iguais, RAM removida/raizRO/UIoff/PCMclosed/
p1p3off; sem save/reboot/imagem/instalação/Deck. Prova batch-run, fontes C119
congeladas preservadas. Próximo: contexto vinculado à prova C120 e uma rodada
gráfica load-only com A/Start/direcional/Fn+L2/Fn+Start quando usuário disponível.

**C121 PREPARADO/OBSERVADO sem GUI,09/11/2026:** [contexto](phase4-batch-graphics.md),
oito checks offline executam os loops reais com quatro bibliotecas e zero
uploads, mais admissões positivas/negativas de análise/prova C120. Corrige a
colisão entre NAMES do bundle seis e do provider quatro encontrada no harness
C120 pendente, sem reescrever fontes/prova congeladas. Novo entrypoint
run-phase4-batch-graphics; binds explícitos ao C120 nativo/bundle/checks.
Observação somente leitura do83 passou guard191/infra, sem preparar ou rodar
cápsula/GUI. Adaptadores de análise/fechamento preparados, CLI help e recusa
de estágio C120 aprovados; sem análise de sessão inexistente/prova gráfica.
Próximo: ciclo observado e qualificação desses adaptadores quando usuário disponível; C120 direto
não deve ser usado como harness gráfico. Sem nova imagem/instalação/Deck.
