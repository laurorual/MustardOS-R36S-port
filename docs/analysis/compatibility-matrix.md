# Matriz de compatibilidade: muOS nativo no R35S

**Atualização C104,05/11/2026 — fluxo após reboot aprovado:**
[Transição normal78→79](phase4-reboot-layout-session.md), UUID novo e identidade4
conferidos, layout C102 preservado. 22casos novos; menu→GB→menu, imagem/input/
áudio/restauração/saída confirmados fisicamente,1084frames, snapshot idêntico.
RootRO0755/PCMclosed/p1p3off/UIoff, hardware/preferências/infraestrutura/mountinfo
restaurados e cápsula removida. Observador não lê seeds nem refaz C97; reboot
normal usa o bootstrap C07 já instalado. Boot frio/autostart/longa duração
seguem pendentes. Deck fora do fluxo; cartão original32 preservado.

**Atualização C103,05/11/2026 — fluxo com layout instalado aprovado:**
[Sessão nativa](phase4-native-layout-session.md) boot78: worker original C77,
sem copiar/bindar /etc ou /mnt inteiros pelo contorno C99. Menu→GB→menu,
imagem/direcional/som/restauração/saída confirmados fisicamente;1160frames e
snapshot idêntico, sem save. 26casos novos; layout C102/rootRO0755 preservados,
PCMclosed/p1p3off/UIoff, hardware/preferências/infraestrutura/mountinfo
restaurados e cápsula removida. CSV recente59,9401Hz e três underruns não
qualificam desempenho sustentado. Novo boot/autostart/longa duração pendentes.

**Atualização C102,05/11/2026 — layout instalado no console:**
[Instalação aditiva](phase4-c79-layout-install.md) aprovada no boot78:
/etc/asound.conf444bytes0644 e /mnt/mmc0755 vazio. 35casos de transação e
recuperação passaram; execução nativa0 e raizRO0755,141arquivos protegidos,
template, fingerprint privado, infraestrutura e montagens preservados.
PCMclosed/p1p3off, cápsula removida. Sem migração integral, reboot ou teste
de jogo; caller sem o contorno C99 e novo boot deste layout ainda pendentes.
Steam Deck não necessário nem acessado; original32 preservado.

**Atualização C100,05/11/2026 — layout offline corrigido:**
[Fábrica derivada](phase4-c79-layout.md) acrescenta /etc/asound.conf644 com os
444bytes do template existente e diretório /mnt/mmc755 vazio. 29casos ext4
reais32MiB passaram; composição real512MiB teve fsck0/releitura3406entradas,
delta exato, fonte/UUID/features/geometria preservados. Sem provisionamento ou
instalação no console; não substitui qualificação nativa do layout instalado.
Deck limpo manualmente conforme confirmação do usuário; backups locais mantidos.

**Atualização C99,05/11/2026 — fluxo instalado C79 aprovado:**
[Sessão temporária](phase4-c79-session.md) no boot78: menu→GameBoy→menu,
imagem/direcional/som/restauração Fn+L2/saída Fn+Start confirmados pelo usuário.
Host/provider4/core instalados,1001frames, snapshot idêntico, nenhum novo save.
38casos novos e ensaio nativo aprovados. Dois pontos ausentes na C79
(/etc/asound.conf e /mnt/mmc) exigiram visões privadas em RAM; a raiz continua RO
e a imagem não foi modificada. Hardware/preferências/mountinfo/infraestrutura
restaurados, cápsula removida e página final. Prova `c79-session` congelada,
26arquivos/3ancestrais conferidos. Layout permanente ainda precisa
correção antes de autostart; frontend geral/longa duração não qualificados.

**Atualização C97,05/11/2026 — primeiro boot C79 aprovado:**
R35S192.168.15.8/boot78 após migração C94. [Coleta somente leitura](phase4-initial-boot.md)
aprovou guardas141hashes/metadados, identidade4, root0755/ext4RO, p1/p3 desmontadas,
PCM fechado, sem UI/BT/.once. Seed NC2048bits consumido sem crédito, RNG pronto,
novo seed creditável256bytes e seeds anteriores ausentes. Coleta inicial expirou
antes de SSH; repetição justificada passou no mesmo boot sem escrita/reboot.
Prova `initial-boot-native` congelada (14arquivos/5ancestrais). Não houve novo
teste de áudio/jogo/controles nem qualificação de todas revisões de hardware.

**Atualização C94 nativo,05/11/2026 — migração inicial C79 aprovada:**
Composição atual76→77, deploy e escrita512MiB somente p2 concluídos; releitura
fria e complemento MBR/p1/p3 integralmente iguais. Coleta independente de recibos,
journal e novo fence aprovada, RO/guard/unmounted/semhelpers conferidos.
Prova `p2-initial-native` congelada. Observador host interrompido antes de coletar;
coleta manual concluída sem repetir writer. Primeiro boot78 e [coleta C97](phase4-initial-boot.md)
ainda pendentes; 25casos offline e lineage real positivos passaram. Original32
preservado; test128 liberado para transferência supervisionada ao R35S.

**Atualização C95/C96,05/11/2026 — novo automount reparado:**
Deck sem regra temporária montou p2/p3RW e tornou raízes0777 no boot76.
[Proteção C95](phase4-card-rearm.md) passou27casos e execução física, com guarda
restaurada, RO e preimage atual independente. [Reparo C96](phase4-root-repair-current.md)
passou29casos e execução física:6bytes alterados/1024bytes nos dois setores,
root0755, fsck0, prefix/SB/GDT/userdata preservados, RO/guard e nenhum mount/helper.
Provas card-rearm-native/root-repair-current-native congeladas; C83 e original32
preservados. Próximo: captura C86 atualizada no Deck, composição/migração C79.

**Atualização C94,05/11/2026 — entrada inicial preparada offline:**
[Executor e coleta finitos](phase4-p2-initial.md), separados da recuperação C89,
passaram84casos (43entrada/41transporte). Ext4 sintético32MiB, adaptadores de
cartão substituídos; sem nova candidata de produção/deploy/escrita/boot C79.
Mains positivos completos ainda não exercitados. Captura73 antiga recusada
antes de SSH/RNG/estágio; prova p2-initial-prepared congelada. Estado real:
R35S192.168.15.16/boot76, CID test128, root0755/RO e idle. Próximo: captura
atualizada offline no Deck com fence C89 existente. Original32 preservado.

**Atualização C93,05/11/2026 — preparador e callback inicial:**
[Preparação da migração](phase4-initial-preparer.md) passou30casos com ext4
sintéticos reais; atualidade de fence/boot/captura, backups privados e scans
por descritores. Backup host12arquivos e factory C79 foram reconferidos por
leitura; captura73 antiga recusada antes de container/RNG/estágio. Sem acesso
ao dispositivo/rede, main positivo completo, nova candidata/deploy/fence/boot.
Entrada privilegiada inicial e coleta ainda pendentes; manter cartão no R35S.

**Atualização C92,05/11/2026 — composição inicial offline:**
[Compositor C79 com estado atualizado](phase4-initial-migration.md) passou25casos
em ext4 sintéticos reais: árvore pública da fábrica, identidade/EAs/históricos,
seed fresco sem crédito e contador reservado, falhas sem conclusão/repetição.
Sem nova candidata512MiB de produção, acesso a cartão/rede, escrita física,
fence ou boot. Preparador/controlador físico inicial continuam pendentes;
C79 ainda não liberada. Cartão pode permanecer no R35S durante a preparação.

**Atualização05/11/2026 — recuperação C89 e primeiro boot aprovados:**
escrita512MiB p2, leitura fria e complemento MBR/p1/p3 integralmente iguais;
próximo fence coletado independentemente antes da entrega. Boot75 C07 passou
por SSH, incluindo arquivos/identidade/root0755/RO/p3 desmontada e caminho
seedless com consumo sem crédito, readiness e novo seed salvo. [Evidência e
limites](phase4-p2-recovery-boot.md). Sem novo ensaio de áudio/jogo, sem migração
C79. Deck ainda necessário; original32/backups preservados. Encerrado por
pedido do usuário para desligar o computador.

**Atualização C89 em execução,04/11/2026:** C86 pós-boot físico e scan C85
independente aprovados no contador73; recuperação regular compôs contador74,
seed novo sem crédito e fsck0, sem alterar identidade/árvore pública. Helper
p2-only iniciado no Deck, ainda sem conclusão de recuperação ou novo boot
qualificados. Observador sem sudo passou17casos e fará coleta/publicação uma
vez ao término, mantendo falhas sem retry. Ver [estado nativo](phase4-p2-recovery-native.md)
e [checkpoint](phase4-resume-checkpoint.md); C79 continua sem liberação.

**Atualização C87–C90,04/11/2026 — controlador preparado e boot73 conferido:**
[C87](phase4-p2-controller.md) passou16+46+24casos e ensaio de escrita512MiB
em loop real. [C90](phase4-p2-card-readiness.md) passou17+19casos e qualificou
no MMC real o claim O_RDWR/transição RO e três leituras integrais iguais da
p2, sem payload. [C89](phase4-p2-recovery.md) passou75casos offline; recuperador
físico completo ainda não executado. Provas separadas e sanitizadas preservadas.
C88 é arquivo regular privado com estado72, agora desatualizado após boot73.
Registro C84 foi selado antes do boot de referência C76; boot73 por SSH aprovou
arquivos instalados/root0755/RO/p3 desmontada/PCM fechado/RNG inicializado.
Desligamento normal solicitado, retorno físico ao Deck aguarda usuário.
Captura real pós-boot, recuperação física e boot posterior continuam pendentes;
isso não libera migração C79. Original32 e backups preservados.

**Atualização C87 parcial,04/11/2026 — núcleo offline:**
[Primitivo p2-only](phase4-p2-write-core.md) passou16casos com descritores
virtuais. Não qualifica controller físico, desbloqueio RO, gravação ou bootC79.
Rodada encerrada por pedido do usuário/limite3%; nenhuma mudança no cartão.

**Atualização C86,04/11/2026 — captura física somente leitura:**
[Helper reference/postboot](phase4-physical-capture.md) passou48casos e uma
captura física de referência no Deck: p2 de512MiB, fsck0, contador72, seis
privados e3.669entradas. Cópia host/hash/fsync e nova análiseC85/árvore completa
iguais; MBR/prefixo e fontep2 estáveis. Cartão desmontado/kernelRO/regraC83
intactos, snapshot root removido. Sem payload escrito/seed/boot/p3; original32/
backups/SDK/imagens intactos. Modo pósboot exige fence anterior e só foi testado
em protocolo sintético. Writer p2-only e ciclo físico de recuperação ainda
pendentes; C79 não liberada para gravar/bootar. Manter cartão no Deck.

**Atualização C85,04/11/2026 — snapshots regulares:**
[Coletor/compositor de recuperação](phase4-recovery-image.md) passaram em36casos
com ext4 sintéticas e código de produção. Reference real C82 de512MiB passou
fsck0/3.669entradas/seis privados/nove históricos, fonte intacta. Árvore pública,
identidade, links e EAs conferidos; históricos consumidos preservados sem rearmar
.once. EAs externos em privados substituídos são recusados. Normalização777→755
agora exercitada com inode explícito; ressalva da fixture C84 documentada, sem
alterar a validação física C83. Não qualifica captura física pósboot, recuperação
no cartão ou bootC79; esses backends continuam pendentes. Sem SSH/cartão nesta
etapa; original32/SDK/backups intactos, manter proteçãoC83 no Deck.

**Atualização C84,04/11/2026 — recuperação preparada offline:**
[Contrato e payload](phase4-root-recovery.md) passaram em85casos, incluindo
ext4 sintéticas reais, contador reservado, seed novo sem crédito, árvore
pública/rede preservadas e política real com stubs sem carga no RNG. Vínculos
C82/C83 e fonte da política C79 conferidos. Ainda faltam coletor pósboot,
compositor de imagem de produção e backend físico; não qualifica restore,
boot ou migração C79. Nenhum seed/fence/candidata real criado. Deck confirmado
com cartão desmontado/kernelRO/regra C83; original32 preservado.

**Atualização C83,04/11/2026 — reparo no Steam Deck:**
[modos das raízes](phase4-root-permissions.md) corrigidos para root:root0755
no test128 por dois setores512, seis bytes de modo/checksum. Prefixo640MiB
pós-hash previsto, fsck0 e nove prefs/saves iguais; cápsulas independentes
Deck/host e backups C82 preservados. 44casos passaram. Cartão desmontado,
quatro aliases kernelRO e regra temporária de automount por CID; SteamOS
permanente intacto. Sem firmware/provisionamento/seedload/reboot; recuperação
pósboot monotônica continua pendente antes de C79. Não qualifica atomicidade
flash, todo conteúdo118GiB p3, outros leitores/cartões/painéis. Original32
permanece fora do fluxo.

Análise estática em 23/10/2026. Alvo inicial: R35S genuíno, RK3326/Cortex-A35, DT model `R36S-V12 2023-08-18 Panel 0`. A direção recomendada é criar um perfil próprio e preservar os componentes nativos do muOS. Os perfis RK3326 existentes são referências parciais; nenhum deles constitui suporte confirmado ao alvo.

**Atualização da Fase 1:** o levantamento do usuário foi complementado por SSH: kernel 4.4.189, userspace AArch64, glibc 2.41 (`2.41-12+deb13u4`), root Btrfs, boot vfat e `/tmp` tmpfs executável. O muinput compilado com sysroot cross Debian trixie executou `--list-devices` com status 0, após conferência de 95 símbolos fortes e do loader. Isso valida somente esse artefato/caminho no Debian atual. Detalhes e hash no [relatório da Fase 1](phase1-muinput.md); a matriz abaixo preserva as evidências da análise inicial e não transforma o teste CLI em validação de tela, input ou firmware.

**Atualização da Fase 2:** [ensaios de display/input](phase2-display-input.md) confirmaram framebuffer 640×480/32 bpp, backlight máximo 160, SDL efetivamente carregada 2.32.10 customizada, KMSDRM + Mali-G31 com renderer `opengles2`/vsync a 59,90 fps. O modo CRTC ativo calcula 59.935683 Hz e difere dos DTBs estáticos. Musplash precisou de patch para usar leitura/escrita quando mmap retorna EINVAL. O perfil de input próprio `rk-r35s-p0`/produto 0x3504 executou com uinput real em namespace privado, sem copiar swaps/inversões G350. Cobertura, direções e retorno ao centro passaram; a sequência estrita mantém uma ressalva de L3 duplo isolado, com repetição de conferência correta. Isso não valida o frontend completo nem outro rootfs/painel.

**Atualização da Fase 3:** o [menu nativo](phase3-native-menu.md) apresentou e navegou após corrigir GUID/índices SDL; A/B/Fn e seleção de Informações foram confirmados. Após a [interrupção](phase3-storage-stop.md) por erros MMC/Btrfs e a [recuperação autorizada](storage-recovery.md), a [retomada de áudio](phase3-audio-resume.md) validou navegação/confirmação audíveis, Fn/B com WAV de controle e encerramento sem cortar a confirmação. Mixer e serviços foram restaurados nas três execuções, sem novos erros de kernel/Btrfs. **Ressalva:** os WAVs originais de ajuda continuam inaudíveis no speaker e o pacote mantém esses recursos; sua adaptação continua pendente. Musplash/mmap permanece excluído. O recorte funcional do primeiro menu está validado, sem aprovação de frontend completo, estabilidade prolongada, firmware ou outro rootfs. A ocorrência isolada de L3 foi aceita pelo usuário como margem de erro até eventual recorrência.

**Atualização da Fase 4:** a [investigação BSP](phase4-bsp-foundation.md) fixou Linux/Linaro/exFAT por commit e compilou uma candidata `4.4.189-muos-r35s-p4`, com 555 módulos AArch64. Um DTS Panel 0 próprio passou na comparação estática com a referência, excluindo OPPs de overclock e modos não testados. Foi recuperada uma cópia de configuração do rootfs, escondida pela montagem FAT de `/boot`; seus recursos coincidem com os da prova. O `Image` instalado difere dos binários locais, e o commit/reprodução exatos e boot da candidata continuam não comprovados. Buildroot gerou sysroot e rootfs headless: 223 ELF AArch64, ext4/fsck e QEMU Cortex-A35 passaram. Um probe da nova libc passou no BSP instalado, com loader/libs próprios em tmpfs ([evidências](phase4-rootfs.md)). O [incremento core/áudio](phase4-core-audio.md) passou a 248 ELF e recompilou muvarctl/mulog/muinput/fnv1a para o sysroot próprio; cache e ciclo de vida D-Bus/PipeWire/WirePlumber passaram no BSP instalado. O sink real é `alsa_output.platform-rk817-sound.playback.0.0`. Os três bipes foram ouvidos somente a 100% de software, ainda baixos; volume confortável e uinput real desse build seguem pendentes. Boot do rootfs, init muOS completo, GPU/SDL/licenças e cadeia de boot permanecem em andamento. A [leitura da cadeia instalada](phase4-boot-chain.md) identificou trust idêntico ao ref, idbloader/U-Boot divergentes e base `5606e804ff-dirty`; o DTS U-Boot fonte de mesmo nome também diverge do Panel 0. A [candidata gráfica](phase4-graphics.md) tem configuração/downloads verificados e build separado em andamento, ainda sem teste no console.

**Retomada da Fase 4 com o usuário:** ALSA/S16, ALSA/S32 e PipeWire produziram grupos igualmente baixos e audíveis, com Playback 95,95 amostrado durante cada PCM; a hipótese de atenuação exclusiva de PipeWire não foi observada nesse recorte ([comparação](phase4-core-audio.md)). A candidata gráfica passou em build/ELF/ext4/QEMU, mas falhou nativamente antes de criar EGL: userspace Mali UK 10.6 versus kernel 11.7. O header ioctl efetivamente compilado no BSP candidato também define 11.7; a referência anterior a 10.6 era de um header legado. Provider gráfico compatível/licenciado continua pendente ([evidências](phase4-graphics.md)). Mixer/serviços foram restaurados, taint ficou 0 e contadores Btrfs zerados; o usuário confirmou o launcher funcional.

**Avanço posterior da Fase 4:** o [muinput do sysroot próprio](phase4-native-input.md) criou e removeu o controle via ABI legada, capturou todos os controles solicitados e liberou o grab; L3 teve um único par. O ZIP Hardkernel r13p0 fornecido pelo usuário conferiu com o hash da receita Batocera e contém o mesmo blob AArch64 instalado. Um [overlay de diagnóstico](phase4-r13-runtime.md) com esse binário passou em QEMU/link, EGL/GLES/readback e SDL/KMSDRM na tela a 59,884 fps, com confirmação visual. O ZIP não contém licença e o overlay não foi integrado à imagem Buildroot: compatibilidade de runtime deste recorte foi testada, enquanto redistribuição, provider SDK/target e firmware completo continuam pendentes. As provas negativas do provider anterior permanecem preservadas.

**Primeiro menu no userspace próprio, 25/10:** [build e ensaios](phase4-menu-own-rootfs.md) recompilaram dependências/frontend para o SDK Buildroot, com base de 274 ELF AArch64, QEMU/link e fsck aprovados. Menu, A/B/Fn e áudio SDL/PipeWire passaram com confirmação do usuário; ajuda usou WAV de controle. A restauração inicial do áudio divergiu (153→95), foi reparada e passou em regressão automática com conferência após subir os serviços. O uso de r13p0 continua como overlay privado, sem licença de redistribuição fechada ou provider final integrado; volume/brilho reais, init/storage e boot próprio permanecem pendentes.

**Candidata privada integrada, 25/10:** por decisão do usuário, os termos pendentes serão consolidados em Markdown ao fim do projeto; uso atual restrito ao desenvolvimento privado ([registro](../../port/packaging/pending-licenses.json)). O [provider r13p0](phase4-private-foundation.md) agora integra SDK e target pela mesma receita, com SONAME/strip reproduzidos e conferidos. A imagem reconstruída passou em 281 ELF AArch64, fsck e QEMU/GBM/carregamento da UI ampliada, sem iniciar seus módulos. O storage de uma única mídia e a guarda de inicialização passaram nativamente em tmpfs, incluindo falha/rollback, identidade dos binds e start/stop. O primeiro ensaio foi invalidado por ausência de `stat` e a repetição passou após corrigir dependência e comparação. Esse teste não acessou blocos, GPU, input ou áudio nem parou o launcher. Não aprova boot, ext4 persistente, SD2, energia ou frontend ampliado em execução. As atualizações anteriores descrevem seus checkpoints históricos.

**Frontend ampliado, 25/10:** o [novo ensaio](phase4-full-frontend.md) executou o frontend e seus submenus no userspace próprio, com mapping nativo SDL, `assign.sh`/521 associações e recursos fixados por blob. Tela, áudio e ajustes reais de volume/brilho foram confirmados. Foi detectada e corrigida leitura dupla de volume físico+virtual: o board R35S agora usa apenas o caminho normalizado no `muhotkey`, preservando outros boards e o índice PMIC. A repetição confirmou um passo por toque; ajuda usou WAV de controle. O resultado ainda depende de recursos/patch aplicados ao staging, a incorporar na próxima imagem. Não valida boot, kernel candidato, emuladores, energia, blank/suspend ou som original da ajuda. Sessões temporárias removidas, mixer/brilho restaurados, serviços ativos e saúde do kernel/Btrfs sem novos erros.

**Serviços de inicialização, 25/10:** [S96/S99 e supervisor](phase4-init-services.md) passaram no rootfs próprio em RAM: espera de input, mapping nativo, first_paint novo, parada/falhas e recolhimento de helpers com setsid/duplo fork. UI, áudio e ajustes reais foram confirmados novamente; a ajuda original continua baixa/estranha e não aprovada. A candidata de283 ELF tem autostart configurado e auditoria host aprovada; coldplug/boot do kernel candidato, módulos/firmware, energia e conteúdo continuam pendentes. O startup do dArkOSen não foi modificado.

**Módulos/firmware e DTB U-Boot, 25/10:** a [imagem atual](phase4-modules-firmware.md) contém 284 ELF userspace e 555 módulos AArch64 do mesmo build de kernel. ET_REL/vermagic, dependências, símbolos via System.map, índices kmod 33, consultas AArch64/QEMU e fsck passaram. O dongle 0bda:c820 observado usa 8821cu e btusb/btrtl; dois firmwares Bluetooth com termos do pacote Debian exato acompanham avisos, e o autoload rtk_btusb está bloqueado. Coldplug e Wi-Fi/BT na candidata não foram testados. O [DTS U-Boot próprio](phase4-uboot-panel.md) passou na comparação estática de display com o Panel0 instalado; isso não compila nem aprova o executável. O fonte base contém seleção de DTB por ADC e recovery SPI/erase automático, a remover antes de qualquer boot candidato. A imagem e todos os 555 módulos continuam sem boot/carregamento no console; o dArkOSen foi apenas consultado.

**Monitor nativo aprovado, 25/10:** a [continuação de memória/boot](phase4-memory-monitor.md) protege o DTB de controle em sysmem e LMB, com testes dos alocadores nativos e UBSan. Após preparação autorizada do cartão secundário de 128 GB e releitura integral, o usuário confirmou o boot do U-Boot próprio, texto/orientação e endereços de memória; `U-Boot=0x3dd08000` confere com a relocação compilada. Power longo desligou e o cartão dArkOSen original voltou a iniciar. A checagem SSH após reconectar o Wi-Fi confirmou hash do Image preservado, taint 0, cinco contadores Btrfs 0 e serviços ativos. Esta aprovação vale para o monitor no único Panel 0, sem kernel/rootfs/frontend candidatos em boot independente. A imagem do monitor contém somente FAT/DTB/textos e a cadeia pré-kernel. As pendências de memória descritas no marco histórico abaixo foram resolvidas por esta continuação.

**Candidata para primeiro Linux:** o [diagnóstico em RAM](phase4-linux-diagnostic.md) foi preparado para o cartão secundário: kernel/DTB próprios, initramfs de quatro ELF do sysroot e logs FAT protegidos por identidade. Auditorias do host e escrita/releitura passaram. O ensaio físico foi concluído: logs confirmam `4.4.189-muos-r35s-p4`, initramfs próprio, console 640×480/80×30, taint 0 e módulos ausentes. O usuário confirmou a tela; coleta read-only e saúde após retorno ao dArkOSen passaram. Os avisos selecionados de logo/IRQ/ASoC também aparecem no sistema instalado; não são aprovação desses recursos. A ausência de `odroidgo3-keys` é esperada com `CONFIG_KEYBOARD_GPIO=m` e nenhum módulo no initramfs. Ext4 completa, coldplug, eventos de input, áudio/GLES e frontend no kernel próprio continuam pendentes.

**Ext4 nativa B01:** [ensaio fechado](phase4-ext4-diagnostic.md) confirma raiz ext4, gpio_keys/odroidgo3-keys e S90 start/status/stop, com taint 0, root final ro, logs e fsck offline aprovados. O dArkOSen retornou saudável. A comparação de MAJ:MIN foi corrigida para saída raw. A aprovação ainda não inclui init BusyBox, coldplug geral, eventos dos controles, áudio/GLES ou UI no kernel próprio.

**Init e serviços C01:** [prova nativa](phase4-service-diagnostic.md) confirma BusyBox PID 1, cadeia selecionada de serviços, coldplug GPIO, RPC D-Bus, controle muinput/mapping SDL e limpeza, com root final ro, fsck offline e retorno saudável. UI/áudio e Wi-Fi ficaram fora; não é aprovação do rcS completo. Avisos de urandom antes da inicialização do pool requerem tratar seedrng/estado inicial. Eventos, renderer, reprodução, energia e outros painéis continuam sem aprovação nesse conjunto.

**Entropia C02:** [seedless e persistido corrigido](phase4-entropy-diagnostic.md) passaram, com crédito do seed anterior, prontidão antes de udev e geração/rotação nativas. Logs separados identificaram prazo de 5 s insuficiente; corrigido para 60 s, boot persistido passou após 7114 ms. Aviso inicial do próprio seedrng foi preservado e sua saída consumida sem crédito no refresh; nenhum aviso prematuro dos consumidores. Input/parada/root ro/fsck/retorno passaram. Nenhum byte/hash de seed foi coletado. Não aprova rcS completo, shutdown, AT_RANDOM ou qualidade criptográfica do kernel legado.

**Gráficos C03 no kernel próprio:** [ensaio nativo](phase4-native-graphics.md) aprovou EGL/readback e SDL/KMSDRM/opengles2 acelerado/vsync, 640×480, 59,630 fps por 30,002 s, sem falhas de render. Usuário confirmou padrão e retorno ao texto; modo DRM antes/depois idêntico. Entropia persistida/input/parada/root ro/fsck/retorno saudáveis. Prova vale para esta sessão Panel 0; frontend/áudio, demais recursos GLES, outros painéis e estabilidade prolongada continuam sem aprovação nesse conjunto.

**Frontend C04 no kernel próprio:** [boot supervisionado](phase4-native-frontend.md) aprovou S99/supervisor como pai, first_paint novo, menu/submenus/ajuda confirmados e stop controlado. Janela silenciosa de 75 s configurada, sem hotkeys; modo DRM/console restaurados, bind temporário removido, entropia persistida/input/root ro/fsck/retorno saudáveis. Áudio, hotkeys, conteúdo, shutdown normal e rcS completo ainda não aprovados nesse conjunto.

**Áudio básico C05 no kernel próprio:** [três bipes audíveis](phase4-native-audio.md) confirmados na revisão5/BOOT0012, rotaSPK_HP/ganho157/softwareunity, PCM S32_LE/estéreo48k. SPK ficou inaudível em95 e157; não bastou obter status0/PCM ativo. Parada nativa do mulog corrigiu root busy; regra eudev específica corrigiu ID_PATH e aplicação do perfil WirePlumber. RotaSPK/ganho95/software0,35 restaurados, snapshot ALSA pré-core igual, debugfs temporário removido, entropia/input/root ro/fsck/saúde aprovados. Alterações de rota/ganho ainda são diagnósticas; o perfil persistente permanece95/SPK. Não aprova frontend sonoro, nível final calibrado, fones, energia ou outros R35S/R36S. Provas negativas e positivas preservadas separadamente.

**Frontend sonoro C06:** [BOOT0017 aprovado](phase4-native-frontend-audio.md) no kernel próprio com navegação adaptada +8,8dB (pico30000, zero clipping no arquivo), confirmação/back originais e confirmação de controle na ajuda. Menu/submenus/entrada e sons confirmados; SDL/PipeWire S32_LE/estéreo44100/SPK_HP157/unity; restauração de13 hashes/ALSA/cache/binds/logger/rootro, entropia/input/fsck/saúde passaram. Ajuda original, loudness final, fones/hotkeys/energia/longa duração pendentes. C07/BOOT0018 aprovou ejeção real1a2b→c820,8821cu/associação/DHCP, fingerprint comparado e SSH por chave/transferência em RAM no kernel próprio, com raizro/taint0/FAT desmontado. C08 confirmou menu/áudio com SSH simultâneo, infraestrutura preservada e restauração de13 hashes/mixer/cache/DRM/rootro. Reboot automático falhou19/21/24 com USBc820/interfaceFF sem vínculo; reset/reprobe insuficientes. C07r3 recuperou SSH por uma retirada/reinserção física no24, com rootro/chave e registros negativos preservados. Isso não aprova hotplug geral/reconexão longa. C09 passou helpers/hotkeys nativos com valores100→95→100 e brilho80→75→80, SSH simultâneo e restauração de mixer/18hashes/cache/pasta de volume/DRM/brilho/rootro/taint0. Percepção visual de dois passos de brilho e calibração sonora permanecem abertas; escala fonte50→46→50%. Bluetooth, UI permanente, Power/suspend e longa duração seguem não testados. C10 reuniu dados em perfil/receita/hook pós-overlay;10checks de build-host/Kconfig isolado e consumo nativo21hashes pré-core/19estáticos+valores passaram, com confirmação do menu/áudio e restauração. UI autostart permanece0; não valida imagem completa ou init definitivo. C11 validou start/status/stop independente, idempotência e três gerações (visual1/3, ciclo2 não confirmado), leases e restauração21 hashes/mixer/cache/brilho/DRM/volume-store com SSH/infra preservados. Receita inclui cinco utilitários próprios; UIenabled0 permanece e init/shutdown/persistência globais ainda pendem.

## Escopo e qualidade da evidência

**Marco histórico: executável SD auditado antes do ensaio nativo, 25/10:** [U-Boot do port](phase4-uboot-sd.md)
compilou com perfil de monitor Panel0, autoboot desligado, defaults em RAM
e panic sem reboot. Os caminhos automáticos de recovery SPI/erase e os
clientes/comandos legados selecionados foram excluídos. Packers GPL do
fonte geraram contêineres privados, com verificação independente; trust
coincide com a referência instalada. Não houve boot ou acesso ao aparelho.
O fechamento de reservas do DTB de controle e do mapa dinâmico de memória
continua como gate anterior a qualquer teste de mídia.

- **F**: fato observado nos arquivos ou objetos Git locais. Não equivale a validação no aparelho.
- **U**: informação fornecida pelo usuário/`AGENTS.md`: AArch64, dArkOSen Debian 13, DRM/KMS e framebuffer disponíveis, boot FAT e root Btrfs. Não foi coletada novamente no dispositivo.
- **H**: hipótese ou proposta, sujeita a teste.
- **?**: dado ainda desconhecido.

Na análise estática inicial foram lidos `AGENTS.md` e `refs/rocknix/AGENTS.md`, sem executar scripts de instalação/build/atualização, seletores ou serviços, nem acessar o aparelho. O build isolado e o acesso SSH posteriores pertencem à Fase 1 autorizada e estão documentados separadamente. Os refs continuam somente leitura.

### Revisões examinadas

Os HEADs conferem com `docs/analysis/upstream-revisions.txt`:

| Repositório | Commit |
| --- | --- |
| `refs/muos/frontend` | `5e8635b3b485eec9ad2ace141c415fd2df47d8f1` |
| `refs/muos/internal` | `550cc58f9cd3449a17f53ca55efcdc6c473b5a89` |
| `refs/muos/tool` | `d5edf14a54ae6588355a75c67b2d493590f281dc` |
| `refs/darkosen` | `1501b7195e0ab0b51614112de84147d914080b28` |
| `refs/rocknix` | `de7cb4985072eee0d688ee1633b8d07ebb89bba6` |

`internal`, `darkosen` e `rocknix` usam sparse checkout. Arquivos marcados **[Git]** abaixo foram consultados com `git show HEAD:<caminho>`, sem materializá-los. A ausência no working tree não significa ausência no upstream. A numeração citada nesses casos corresponde ao blob do HEAD.

O dArkOSen já apresentava alterações locais em `KERNEL/Image`, `boot/DTB SELECTOR.apk`, `boot/SELECT MODEL.exe`, `boot/low_battery.bmp` e nos quatro `boot/dtb/{640,720,1024,1280}/low_battery.bmp`. Foram preservadas. Portanto, o HEAD sozinho não identifica todos os bytes desses artefatos locais. O DTB Panel 0 analisado não estava entre os arquivos modificados.

## Matriz

| Camada | Evidência muOS | dArkOSen/alvo | Referência ROCKNIX | Avaliação e ação |
| --- | --- | --- | --- | --- |
| ISA e CPU | **F** frontend oferece `ARM64`, A53 e variantes; tool usa tuple AArch64 Buildroot [E6]. | **U** Cortex-A35/AArch64. | **F** RK3326 configura `cortex-a35` [E10]. | Compatibilidade de ISA é plausível; ABI e bibliotecas **?**. Começar com ARMv8-A sem extensões opcionais presumidas. |
| Bootloader | **F** G350 inclui `uboot.img`; Pixel 2 tem kernel/DTB/`boot.ini`; ambos usam `booti` [E1]. | **F** preset Panel 0 carrega `Image`, `uInitrd` e DTB; há DTB separado para U-Boot [E4]. | **F** U-Boot + rkbin e seleção/extlinux [E10–E11]. | Não reutilizar bootloader de G350/Pixel. Layout bruto, DDR, detecção e código de boot do R35S ainda **?**. |
| Kernel/DTB | **F** kernels distribuídos como `package/Image`; fontes completas/configuração reproduzível não estabelecidas nos três repositórios muOS. | **F** KERNEL descreve base `christianhaitian/linux`, branch `rg351`; módulos sob `4.4.189`; DTB Panel 0 contém bindings BSP [E4–E5]. | **F** receita RK3326 aponta para kernel `7.1.2` no snapshot e patches próprios [E10]. | Escolher um conjunto kernel+DTB+drivers. Não misturar DTB BSP com kernel ROCKNIX por nome ou SoC. Versão real do kernel instalado **?**. |
| Initramfs e raiz | **F** presets muOS RK passam `-` no argumento initrd e raiz ext4 [E1]. | **F** preset dArkOSen carrega `uInitrd`; **U** raiz Btrfs [E4]. | Usa sua própria cadeia de initramfs/kernel [E10]. | O initrd do dArkOSen não é requisito universal RK3326; investigar o que ele prepara antes de removê-lo em imagem nova. |
| Partições | **F** comum: raiz ext4, boot vfat, ROM exfat; RK p1/p2/p3 [E2]. | **U** boot FAT, raiz Btrfs; layout completo/UUIDs não coletados. | **F** opções RK3326 usam tabela msdos [E10]. | Não converter cartão atual. Definir layout independente em imagem futura. `mmc 1:1` de U-Boot não prova nome `/dev/mmcblk1` no Linux. |
| PID 1/inicialização | **F** `init=/sbin/init`, scripts `sysinit`, udev, D-Bus, PipeWire e lançamento próprio [E1–E3]. | **F** units systemd, ES como usuário `ark` [E5]. | Stack própria da distribuição. | Fluxo muOS é orientado a scripts; ligação exata de PID 1/`inittab` ao `sysinit` não está estabelecida. Não executar o boot completo sobre Debian. |
| Tela Panel 0 | **F** perfis RK 640×480, porém nós de display diferentes [E7]. | **F** DTB: 640×480, DSI 4 lanes RGB888, sequência de 370 bytes [E4]. | **F** DTS R36S e patch ST7703; overlays para variantes [E11]. | Dados de painel reaproveitáveis como especificação. Timings divergem até entre DTB Linux e U-Boot; validar modelo e modo ativo. |
| Frontend gráfico | **F** LVGL sobre SDL2; solicita renderer GLES2 acelerado + vsync [E8]. | **U** DRM/KMS e fb disponíveis; SDL/EGL/GBM/libmali e renderers instalados **?**. | **F** Mali/Panfrost, Wayland/sway e libmali configurados [E10]. | `/dev/fb0` existente ou splash funcional não prova frontend funcional. Testar SDL/EGL no stack escolhido. |
| Brilho/blank | **F** muOS procura sysfs backlight; valor comum máximo 255; blank usa fb0 [E7]. | **F** DTB Panel 0 declara 161 níveis, 0–160, default 80 [E4]. | **F** DTS base declara 0–255 [E11]. | Não herdar máximo 255 no kernel BSP sem medição. Descobrir `max_brightness`, escala e recuperação de blank. |
| Áudio | **F** PipeWire/WirePlumber, ALSA plugin e nomes de sinks específicos; G350 `digital volume`, Pixel `Speaker` [E7, E9]. | **F** codec RK817; scripts usam mixer `Playback`; hook de resume referencia PulseAudio [E4–E5]. | **F** `rk817_int`, quirk inverte HP/SPK [E11]. | Codec compartilhado ajuda; mixer, detecção de fone, nomes de sinks e rotas não são intercambiáveis. Estado real **?**. |
| Botões/sticks | **F** muinput normaliza para `muOS-Keys`; G350 e Pixel têm mapas próprios [E6–E7]. | **F** DTB usa `GO-Super Gamepad`, F1–F5 em `BTN_TRIGGER_HAPPY*`; watcher Fn reconhece HAPPY5 [E4–E5]. | **F** `r36s_Gamepad`, `rocknix-singleadc-joypad`; Fn `BTN_MODE` [E11]. | Criar backend próprio derivado do evdev portátil, após captura real. Não forçar perfil G350 para “detectar” R35S. |
| Power/volume | **F** Pixel tem `board/vol_name=gpio-keys` e módulo de power vinculado ao build exato [E7]. | **F** DTB PMIC pwrkey ativo; nomes/nós de eventos em runtime **?**. | **F** volume em dispositivo gpio-keys separado [E11]. | Inventariar todos os event nodes. Não copiar `board/event=4`, módulos Pixel ou pressupor volume no gamepad. |
| Uinput/evdev | **F** `/dev/uinput`, evdev com grab; setup uinput moderno e fallback legado [E6]. | Wrapper ES referencia uinput; permissões e configuração do kernel em uso **?** [E5]. | Driver joypad com binding próprio [E11]. | Há caminho legado no código; kernel antigo não significa incompatibilidade automática. Validar ABI de ioctl e liberação de grab no teste futuro. |
| Bateria/carga | **F** G350 usa `/battery/*` + `/ac/online`, Pixel usa `/usb/online`; tamanhos 3200/1800 [E7]. | **F** DTB RK817 tem `design_capacity=3140`; monitor lê `/battery/capacity` [E4–E5]. | **F** simple-battery 3380 mAh e curva própria [E11]. | Não escolher capacidade por família. Confirmar unidade de tensão, presença de carregador, curva e capacidade física. |
| LEDs/rumble | **F** G350 inicializa GPIO15; Pixel usa PWM e scripts específicos [E3, E7]. | **F** monitor aciona GPIO77 para bateria [E5]. | Quirk R36S também menciona GPIO77 [E11]. | GPIO15 não é prova de motor no R35S. Excluir rumble e escritas GPIO do primeiro teste. Números dependem do kernel. |
| Suspensão/desligamento | **F** fluxo muOS tem `mususpend`, halt e scripts por board [E3, E7]. | **F** `finish.sh` desmonta volumes e usa systemd; hook pausa/retoma processos [E5]. | Patches/PMIC próprios da base RK3326. | Não transportar fluxo de shutdown sobre dArkOSen. Testar wake, áudio e display depois do bring-up básico. |
| Configuração/recursos | **F** `/opt/muos`, `/run/muos/storage`, varstore, themes/línguas/fontes; conteúdo `init/` [E2–E3, E8]. | **F** `/home/ark`, `/roms`, ES, gamecontrollerdb e scripts externos [E5]. | `/flash` e `/storage` têm semântica própria [E11]. | Frontend não é binário independente desses recursos. Preparar staging completo; variáveis de diretório não relocam todos os caminhos fixos. |
| Bibliotecas/ABI | **F** frontend liga bibliotecas dinâmicas e arquivos estáticos; muinput é menor [E6, E8]. | **U** Debian 13; loader, glibc, SDL, símbolos e kernel mínimo ainda **?**. | Rootfs ROCKNIX distinto. | Compilar contra sysroot de destino; auditar ELF e dependências transitivas. Mesmo AArch64 e mesmo SoC não bastam. |
| Rede/RTC | **F** perfis RK desativam rede/HDMI e usam rtc0 [E7]. | Wi-Fi/BT são tratados por scripts; presença de adaptador e RTC real **?**. | Firmware e pacotes opcionais [E10]. | Não importar serviços de rede/GPU de outro board; habilitar conforme inventário. |
| Reprodutibilidade | **F** toolchain exemplar e pacotes binários; scripts tool manipulam imagens existentes [E1–E2, E6]. | Fonte parcial de alterações de kernel e artefatos; instalação atual não foi extraída. | Receitas de kernel/U-Boot/DSI úteis [E10–E11]. | Falta fechar proveniência do rootfs/toolchain/kernel muOS. Resolver antes de publicar imagem independente. |
| Licenças | muOS traz GPLv3 e dependências com licenças próprias [E12]. | Licença MIT no topo não relicencia kernel/blobs [E12]. | DTS dual GPL/MIT, scripts GPL, branding separado [E12]. | Registrar origem e licença por componente antes de copiar ou redistribuir. Não importar subsistemas completos. |

## Evidências detalhadas

### E1 — Boot muOS e limites do material disponível

`refs/muos/internal/device/rk-g350-v/package/boot.ini:3–15`:

```text
setenv bootargs "root=/dev/mmcblk0p2 rootfstype=ext4 rw rootwait ... init=/sbin/init"
if test "${hwrev}" = "1"; then
    setenv g350_dtb "rk3326-batlexp-linux1.dtb"
...
load mmc 1:1 ${loadaddr} Image
load mmc 1:1 ${dtb_loadaddr} ${g350_dtb}
booti ${loadaddr} - ${dtb_loadaddr}
```

O diretório inclui `Image`, `uboot.img`, dois DTBs, manifestos SHA256 e assinatura. Isto demonstra distribuição de payload por aparelho, não a receita completa para reconstruir U-Boot/kernel.

`refs/muos/internal/device/rk-pixel-2/package/boot.ini:1–6` usa `root=PARTLABEL=ROOTFS`, `rootfstype=ext4`, `fbcon=rotate:3`, `rk3326s-gkd-pixel2.dtb` e também `booti ... - ...`. Seu DTS e módulos adicionais são específicos do Pixel 2. A rotação de console não estabelece a rotação da UI.

`refs/muos/tool/device.json:1–40` descreve offsets/configurações H700 e A133; não contém descrição de imagem RK3326. Não aplicar esses offsets Allwinner ao Rockchip. Os três repositórios muOS examinados não forneceram uma receita completa identificada de bootloader + kernel + rootfs RK3326 do zero; o exemplo Buildroot em E6 identifica um ambiente esperado, não seu defconfig reproduzível.

### E2 — Rootfs, armazenamento e conteúdo muOS

**[Git]** `refs/muos/internal/device/common/config/` contém arquivos de uma linha:

| Caminho relativo ao diretório acima | Valor |
| --- | --- |
| `storage/root/{type,mount,sep}` | `ext4`, `/`, `p` |
| `storage/boot/{type,mount,sep}` | `vfat`, `/mnt/boot`, `p` |
| `storage/rom/{type,mount,sep}` | `exfat`, `/mnt/mmc`, `p` |
| `screen/bright` | `255` |
| `cpu/governor` | `/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor` |

Os perfis `device/rk-{g350-v,pixel-2}/config/storage/` especificam `mmcblk0`, boot 1, raiz 2, ROM 3. É preciso combinar valores comuns e overrides; copiar apenas a pasta do board deixa campos faltando.

`refs/muos/internal/script/device/storage.sh:45–62` admite `exfat`, `vfat`, `ext4`; outros tipos retornam falha. Trata montagem de armazenamento do muOS, não prova que o frontend C não possa residir em Btrfs. Porém os presets de boot e as ferramentas de raiz esperam ext4.

`refs/muos/internal/script/init/async/S06mount.sh:32–57` monta ROM/SD e faz binds sob `/run/muos/storage`. `internal/README.md:9` descreve `init/` como conteúdo movido na primeira instalação. `script/system/rootfs.sh:102–115` instala/substitui configurações em `/etc`, links para `/opt/muos/share/conf/rootfs` e `resolv.conf` para `/tmp/resolv.conf`.

`refs/muos/tool/update_rootfs.sh:256` calcula offsets de uma imagem existente; `tool/rootfs/grow_rootfs.sh:73,250–281` usa ferramentas de partição/ext4 e recria partição; `tool/populate_disk.sh` popula destinos. São ferramentas de escrita, não sondas para a instalação atual. Não foram executadas.

### E3 — Inicialização e serviços muOS

`refs/muos/internal/script/init/sysinit:23–35,50–103`:

```text
. /opt/muos/script/var/boot.sh
if ! /opt/muos/script/system/rootfs.sh restore; then ...
RUN_INIT_RECORDED start "$INIT_DIR/S10udev.sh" &
RUN_INIT_RECORDED start "$INIT_DIR/S30dbus.sh" &
RUN_BOOT_SERVICE S80pipewire.sh PipeWire &
RUN_BOOT_SERVICE S81mode.sh "Device mode" &
RUN_INIT_RECORDED start "$INIT_DIR/S99muos.sh"
```

Há execução concorrente e readiness, não apenas ordenação por nomes `Sxx`: montagem prioritária inicia no grupo async; `S99muos.sh:90–100,138–163` espera storage, trata modo carga, inicia hotkeys e frontend. `async/S01init.sh:23–66` altera printk/governor, configura ALSA, carrega módulos e inicia bateria. O comentário em `script/system/halt.sh:281` referencia `::shutdown:/bin/umount -a -r` em `/etc/inittab`; isso é evidência de expectativa de init por inittab, não inspeção do PID 1 de uma imagem instalada. O arquivo completo e a integração ao boot ainda precisam ser obtidos.

`script/var/base.sh:7–26` fixa diretórios e `LD_LIBRARY_PATH` para frontend/lib; `script/var/service.sh:135` inicia `mubattery`. Os serviços de rede, Bluetooth, discovery, web e direct link têm funções próprias, mas não são pré-requisitos para o primeiro teste de ABI.

**Risco de execução fora do firmware:** iniciar `sysinit`, `S99muos` ou `rootfs.sh` sobre Debian pode alterar configurações, governor, mounts, módulos e fluxos de energia. O frontend deve ser ensaiado em staging controlado, sem executar esse bootstrap no aparelho atual.

### E4 — dArkOSen, DTB exato e painel

`refs/darkosen/boot/dtb/r36s/R36S-V12 2023-08-18 Panel 0/boot.ini:3–15`:

```text
setenv bootargs "root=/dev/mmcblk0p2 rootwait rw ... fbcon=rotate:0 ... max_cpufreq=1512 boot_cpufreq=1296"
load mmc 1:1 ${loadaddr} Image
load mmc 1:1 ${initrd_loadaddr} uInitrd
load mmc 1:1 ${dtb_loadaddr} rk3326-r36s-linux.dtb
booti ${loadaddr} ${initrd_loadaddr} ${dtb_loadaddr}
```

`boot/dtb/r36_devices.ini:33–40` mantém Panel 0 e Panel 4 como presets distintos. `README.md` orienta preservar tanto o DTB de U-Boot quanto o de Linux. Isso não autoriza executar o seletor ou gravar bootloader.

Os valores abaixo foram decodificados diretamente do FDT binário com leitura Python/stdlib em memória; `dtc` não estava disponível e não foi instalado. A notação DTS é uma transcrição de propriedades, não um novo DTS compilado. Fonte: `.../Panel 0/rk3326-r36s-linux.dtb`, SHA256 `5634eb3eb56883559a91fcb9dbea0958cd3c7ebece9c985907063f36ec070ff2`.

```dts
/* / */
model = "R36S-V12 2023-08-18 Panel 0";
compatible = "rockchip,rk3326-odroidgo3-linux", "rockchip,rk3326";
/* /dsi@ff450000/panel@0 */
compatible = "elida,kd35t133", "simple-panel-dsi";
dsi,lanes = <4>;
dsi,format = <0>; /* valor que importpanel.py mapeia para rgb888 */
dsi,flags = <0xa03>;
prepare-delay-ms = <2>;
enable-delay-ms = <120>;
/* /dsi@ff450000/panel@0/display-timings/60Hz */
clock-frequency = <50000000>;
hactive = <640>; vactive = <480>;
hfront-porch = <450>; hsync-len = <46>; hback-porch = <450>;
vfront-porch = <17>; vsync-len = <5>; vback-porch = <13>;
```

Existem também modos nomeados `50Hz` e `75Hz`. O nome do nó não comprova refresh efetivo. `panel-init-sequence` tem 370 bytes, começa com `39 00 04 b9 f1 12 83` e tem SHA256 `972f614858caa119329cffdafc07c3a610b92343090ee7acf65e68c21d131a91`.

O `rg351mp-uboot.dtb` da mesma pasta tem SHA256 `e65ccee748de35597c3f7f5e3032ed33e8312abba886bd3dba1aa0dbf662d102`, modelo `RG351MP for linux based on Rockchip rk3326` e a mesma sequência de painel, mas `hsync-len=70` e delays/backlight diferentes. **Não são DTBs intercambiáveis.** O patch ROCKNIX também usa hsync 70; essa divergência exige confirmação do modo real e comparação das sequências antes de migração.

Outras propriedades do DTB Linux Panel 0:

| Nó | Propriedade observada |
| --- | --- |
| `/backlight` | `pwm-backlight`, período PWM 40000, 161 níveis com último 160, default 80 |
| `/rk817-sound` | `simple-audio-card`, nome `rockchip,rk817-codec`, I2S, mclk-fs 256, detecção de fone |
| `/i2c@ff180000/pmic@20/battery` | `rk817,battery`, `design_capacity=3140`, `design_qmax=3454`, curva OCV, `monitor_sec=5` |
| `/i2c@ff180000/pmic@20/pwrkey` | `status="okay"` |
| `/odroidgo3-joypad` | `compatible="odroidgo3-joypad"`, `joypad-name="GO-Super Gamepad"`, status ativo |
| `.../sw1–sw4` | D-pad `0x220–0x223` |
| `.../sw5–sw8` | A `0x131`, B `0x130`, Y `0x134`, X `0x133` |
| `.../sw11–sw13` | F3/F4/F5 `0x2c2/0x2c3/0x2c4` |
| `.../sw19,sw22` | F1/F2 `0x2c0/0x2c1` |

Esses dados descrevem o artefato local, não provam que ele seja idêntico ao DTB carregado no aparelho. Capacidade da bateria declarada no DTB também não mede a célula instalada.

### E5 — dArkOSen: software e lacunas do snapshot

`refs/darkosen/KERNEL/README.md:3–10` identifica base `christianhaitian/linux`, branch `rg351`, defconfig `rg351p_tweaked_defconfig` e GCC Linaro 6.3.1. O diretório traz alterações de cpufreq/OPP e módulos `lib/modules/4.4.189/`; não é uma árvore completa de kernel. Na análise estática inicial, o kernel instalado ainda não havia sido consultado. A Fase 4 confirmou `Image` instalado diferente dos dois locais, recuperou a cópia de configuração escondida no rootfs e construiu uma candidata própria a partir da fonte indicada, conforme o relatório vinculado acima. Não transportar overclock de CPU/GPU como requisito do port.

**[Git]** `etc/systemd/system/emulationstation.service:5–12`:

```ini
[Service]
Type=simple
User=ark
WorkingDirectory=/home/ark
ExecStart=/usr/bin/emulationstation/emulationstation.sh
Environment="SDL_VIDEO_EGL_DRIVER=libEGL.so"
```

O wrapper **[Git]** `usr/bin/emulationstation/emulationstation.sh:21–24,37–39` usa gptokeyb, uinput e `XDG_RUNTIME_DIR=/run/user/$UID/`. A unit mostra como iniciar ES, não qual renderer/backend SDL funciona no dispositivo do usuário.

`usr/local/bin/boot_volume.sh:3` executa `amixer -c 0 -q sset Playback 60%`; `mute_toggle.sh` também usa `Playback`. **[Git]** `etc/systemd/system/boot_volume.service` chama o script depois do ES. **[Git]** `lib/systemd/system-sleep/volume-resume-fix:3–14` pausa/retoma ES, aplay e pulseaudio; a presença do hook não comprova que PulseAudio esteja ativo hoje.

`usr/local/bin/fn_menu_watcher.sh:16–19,43–58` encontra `GO-Super Gamepad` por nome e lê `evtest`; Fn/HAPPY5 aciona MENU_TOGGLE via UDP no RetroArch. **[Git]** sua unit roda como root. **[Git]** `OGAGE/README.md:1–15` descreve brilho/volume/gamma/shutdown por hotkeys. `usr/local/bin/batt_life_warning.py:7–11` usa `/sys/class/power_supply/battery/capacity` e GPIO77. `usr/local/bin/finish.sh` desmonta `/boot` e SD2 e pede poweroff/suspend ao systemd.

Esses componentes podem disputar teclas, áudio, LEDs e energia com serviços muOS durante testes. O repositório contém complementos e binários, não um inventário comprovado da instalação Debian 13 em uso. Permanecem pendentes fstab, kernel config, bibliotecas, mixer completo, drivers ativos e serviços realmente habilitados.

### E6 — Compilação e contrato de muinput

`refs/muos/frontend/input/Makefile:7–18` compila `main.c`, `runtime.c` e fontes em `common`, `devices`, `drivers`, com C11, LTO, proteção de stack/FORTIFY; liga `-lm -lrt`. É menor que o frontend completo e não depende de SDL. O alvo `check:38–40` executa o binário: não deve ser usado como check nativo de um artefato AArch64 no host x86 sem ambiente apropriado.

`input/devices/registry.c:14–22` registra G350/Pixel e o board path `/opt/muos/device/config/board/name`; não registra R35S/R36S. `input/README.md:67–96` estabelece `BUS_VIRTUAL`, nome `muOS-Keys`, vendor `0x756d`, version `0x736f` e produtos distintos `0x3501/0x3502`. Um perfil novo precisa de identidade não conflitante e GUID/mapping coerentes, sem usurpar o ID dos existentes.

`input/drivers/evdev/evdev.c:98–100,147` usa `EVIOCGRAB` e libera o grab. `input/common/uinput.c:170–171,232–247` verifica versão uinput e usa setup moderno ou `write_legacy_setup`. Os acessos GPIO/serial/I2C citados no README são por backend; não são todos necessários para o R35S evdev.

`input/main.c:146–151,268–295` trata `--list-devices`/`--help` antes de selecionar backend, criar diretório de runtime ou abrir uinput. Há uma leitura opcional do arquivo de intensidade antes do parser, mas não inicialização de hardware nesse caminho. Esta é a base do primeiro teste proposto no roadmap.

`refs/muos/tool/examples/rk3326-muos-cc.sh:3–30` usa `DEVICE=RK3326`, tuple `aarch64-buildroot-linux-gnu`, sysroot dedicado e `-march=armv8-a+simd -mtune=cortex-a53`. Já `frontend/common.mk:15–55` aceita `DEVICE=ARM64` ou `GENERIC` com `ARCH_FLAGS`; **não aceita `DEVICE=RK3326`**. Separar o nome da plataforma nos scripts tool da seleção de flags no frontend. A53 tuning no exemplo não é prova de ajuste para A35. Preferência inicial: `ARM64`/`-march=armv8-a`; considerar tuning A35 depois de verificar o compilador e HWCAP.

### E7 — Perfis RK3326 reaproveitáveis, com limites

| Campo relativo a `refs/muos/internal/device/` | `rk-g350-v/config/` | `rk-pixel-2/config/` |
| --- | --- | --- |
| `board/stick` | `2` | `0` |
| `board/event` | `4` | `4` |
| `screen/device` | `/dev/dri/card0` | `/dev/fb0` |
| `screen/internal/{width,height}` | `640`, `480` | `640`, `480` |
| `screen/refresh` | `60.303` | `60.082` |
| `screen/rotate`, `sdl/rotation` | `0`, `0` | `0`, `0` |
| `audio/control` | `digital volume` | `Speaker` |
| `battery/charger` | `/sys/class/power_supply/ac/online` | `/sys/class/power_supply/usb/online` |
| `battery/size` | `3200` | `1800` |
| `board/network`, `board/hdmi` | `0`, `0` | `0`, `0` |

**H:** G350 é ponto de partida estrutural mais próximo para UI 640×480 e dois sticks; Pixel 2 ajuda a entender sysfs, fb e power, mas seu hardware não equivale ao R35S. Ambos apontam `sdl/name=muOS-Keys`. As strings de sinks em `audio/pf_internal` diferem até entre esses dois perfis.

`refs/muos/frontend/input/devices/evdev/portable.c:135–140,317–339,363–390`:

```text
{"rk-g350-v", "g350_joypad", ... layout_g350, ...}
{"rk-pixel-2", "pixel2_joypad", ... layout_pixel2, ...}
```

G350 converte HAPPY1/2 para Select/Start e HAPPY3/4/5 para L3/R3/Menu, troca A/B e reorganiza/inverte eixos. Isso combina parcialmente com o DTB BSP do R35S, mas a transformação de eixos e o source name precisam de perfil próprio. ROCKNIX já emite códigos distintos, exigindo mapeamento específico por stack escolhido.

`internal/script/device/module.sh:141–170` inicia muinput para RK e condiciona o módulo power do Pixel a `uname -v` exato. `device/rk-pixel-2/module/README.md` registra esse acoplamento. Nenhum `.ko` deve ser transportado para o R35S sem reconstrução contra seu kernel/config/símbolos.

`internal/script/var/display.sh:209–245` tenta sysfs backlight para `setbl` e só usa fallback Allwinner em certas famílias. `script/device/bright.sh:47–65` escreve blank em `/sys/class/graphics/fb0/blank`. Paths de cor `screen/colour` herdados de `/sys/class/disp/...` nos dois perfis não provam existência dessa interface no R35S.

### E8 — Requisitos do frontend e ferramentas de build

`refs/muos/frontend/common.mk:84–104`:

```make
COMMON_LIBS = -lcurl -lSDL2 -lSDL2_mixer -lSDL2_ttf -lSDL2_image -lharfbuzz -lfreetype -lpthread -lpng -lm
# binários: RUNPATH $ORIGIN/lib; bibliotecas próprias: $ORIGIN
```

São necessários toolchain C/C++, make, ccache e sysroot coerente. `README.md` também lista ferramentas de download/extração e geração. `external/build.sh:7` constrói FFmpeg, libarchive, mojibake, OpenSSL, openmpt, gme, sidplayfp, vgmstream, variante FFmpeg de vídeo e rcheevos. `external/external.mk` liga arquivos estáticos desses componentes; isso **não torna o executável todo estático**, nem elimina ABI de libc/SDL/EGL e dependências transitivas.

`Makefile:7–12,33–49,99–131` organiza módulos/daemons/tools e bibliotecas próprias, LVGL/PlutoSVG, host libretro, terminal, vídeo e overlay. Em ARM, o prebuild inclui `mugl`, descrito no próprio Makefile como forwarder GLES de 32 bits para TrimUI; evitar que esse caminho dite requisitos desnecessários do primeiro teste AArch64.

`build.sh:845–859` faz `chmod -R`/`chown -R` e prechecks; `README.md` documenta geração, formatação e escrita no repositório irmão de idiomas. `Makefile:51–52` cria diretório durante avaliação. **Nem `make -n` no checkout de referência é garantia de somente leitura.** Builds futuros devem usar cópias de trabalho em `build/`, nunca estes refs.

`common/platform/display.c:712–765` usa SDL, hint `opengles2`, janela fullscreen e renderer acelerado/vsync; falhas de criação encerram execução. LVGL é toolkit da UI, não um substituto para drivers SDL/EGL. `module/musplash.c:172–194` tem caminho framebuffer direto e é útil como teste de tela separado.

`common/config/var_store.c:669–700` permite overrides de configuração/cache, mas `input/devices/registry.c:22` e scripts ainda fixam `/opt/muos`. Uma variável isolada não torna todo o firmware relocável. Para rodar o menu, preparar configuração comum+board, varstore, bibliotecas, temas, idiomas, fontes e diretórios de runtime/conteúdo, auditando escritas e callbacks de energia.

### E9 — Áudio e serviços muOS

**[Git]** `refs/muos/internal/share/conf/rootfs/asound.conf:1–29`:

```text
pcm.!default {
    type plug
    slave.pcm {
        type pipewire
        playback_node "-1"
...
ctl.!default { type pipewire }
```

`script/init/S80pipewire.sh:324–354,455–458` prepara WirePlumber, inicia PipeWire e restaura configs ALSA. Requer processos, plugins, D-Bus e permissões/scheduling adequados, além do driver ALSA do codec. `mubattery` atualiza bateria a cada três segundos (`frontend/module/mubattery.c:13–24`); `muhotkey`, `muremap`, `mususpend`, `mudisp`, `muvarctl` devem ter seus acessos auditados individualmente. Compilar todos não é necessário para testar uma CLI, e iniciar todos no Debian não é um teste isolado.

Os nomes abaixo incluem serviços e ferramentas auxiliares; nem todos são daemons permanentes. Os módulos seguem a ligação compartilhada de `frontend/Makefile:145–158`, enquanto tools têm fontes/libs por alvo (`:174–178`). Assim, usar framebuffer direto não implica que o alvo upstream de `musplash` dispense as dependências de link do frontend.

| Componente | Requisitos/evidência adicional em `refs/muos/frontend/` | Implicação para o port |
| --- | --- | --- |
| `muvarctl` | `Makefile:21`, `common/config/var_store.c:669–700`: configuração por arquivos e cache de runtime. | Preparar configuração comum+board e diretórios graváveis; não assumir que paths de todos os componentes acompanhem seus overrides. |
| `mubattery` | `common/platform/battery.c:14–24`: config `/opt/muos/device/config/battery`, saída `/run/muos/battery`. | Exige fontes sysfs corretas, curva/unidades e escrita em runtime; não basta executar o monitor sem configuração. |
| `muhotkey` | `module/muhotkey.c:1–23,625–627`: bibliotecas comuns, JSON, evdev; abre event nodes. | Mapear power/volume e ações; coordenar com ogage/Fn/gptokeyb antes de habilitar. |
| `muremap` | `module/muremap.c:6–9,199`: SDL2, gamecontrollerdb global/usuário e escrita de mapping. | Validar GUID/identidade virtual e limitar arquivos de saída ao staging de teste. |
| `mudisp` | `module/mudisp.c:14–27,109–121`: `/dev/disp`, ioctls próprios de configuração/layers e fb0. | Não é um controlador DRM/KMS genérico. Não requerê-lo para o R35S sem evidência dessa interface; brilho já tem caminho sysfs. |
| `mususpend` | `module/mususpend.c:351–422,477–566`: policies CPU, online de CPUs, `/sys/power/state` e `wakeup_count`. | Precisa de suporte PM/wakeup e privilégios; altera estado global, ficando para testes de energia posteriores. |
| `murgb` | `module/murgb.c:23–28`: led_anim, singleadc-joypad, ttyS5 e MCU AXP2202. | São interfaces específicas de outros aparelhos; presença do binário no build não estabelece recurso RGB no R35S. |
| `mudns`, `mulink`, `muweb`, `muverify` | `Makefile:9–27`: daemons opcionais de discovery/link/web e verificação com libcrypto estática. | Adiar rede/USB/web até o sistema básico; manter verificação/proveniência na integração de firmware e atualização. |

### E10 — ROCKNIX como referência de hardware e build

`refs/rocknix/projects/ROCKNIX/devices/RK3326/options:7–41,55–74` configura A35, kernel arm64, U-Boot/rkbin, Mali G31, `mali panfrost`, Wayland/sway e `libmali generic-dsi device-switch`. Isto é descrição do snapshot, não validação da imagem no R35S do usuário.

**[Git]** `projects/ROCKNIX/packages/linux/package.mk:18–19,43–47,82–83,110–118` seleciona RK3326 `7.1.2`, acrescenta patches `rocknix-joypad`/`mainline-rockchip`, incorpora `panel-generic-dsi.c` e copia DTS do projeto. Não se deve adivinhar que este checkout usa uma versão antiga do kernel por se tratar de RK3326; a receita local foi consultada. A disponibilidade/compilação dessa versão externa não foi verificada.

`projects/ROCKNIX/devices/RK3326/packages/u-boot/package.mk` e `sources/configs/rk3326-handheld_defconfig` mostram build de bootloader específico, com variantes. Reutilizar esse conhecimento exige reconstruir uma cadeia coerente para o port, não copiar todo o sistema ROCKNIX.

### E11 — ROCKNIX: família e painéis

`refs/rocknix/projects/ROCKNIX/devices/RK3326/linux/dts/rockchip/rk3326-gameconsole-r36s.dts:7–28`:

```dts
#include "rk3326-gameconsole-r3xs.dtsi"
#include "rk3326-device-group-r36.dtsi"
model = "Game Console R36S";
compatible = "gameconsole,r35s", "gameconsole,r36s", "rockchip,rk3326";
/* joypad */
compatible = "rocknix-singleadc-joypad";
joypad-name = "r36s_Gamepad";
```

O mesmo DTS define ADC multiplexado para quatro eixos, GPIOs de botões e Fn `BTN_MODE` (`:36–79,144–147`). O include `rk3326-gameconsole-r3xs.dtsi:26–138,194–238` define PWM backlight, gpio-keys de volume, bateria, RK817, DSI e painel `gameconsole,r36s-panel`/`sitronix,st7703`.

`patches/linux/001-panel-updates.patch:133–218,230` adiciona sequência R36S e modo 640×480/50 MHz, hsync 70, quatro lanes RGB888. Não há prova de equivalência completa com o preset dArkOSen “Panel 0”; comparar comandos, delays, polaridades e timings e testar fisicamente.

`packages/u-boot/config/overlays/README.txt:1–6` informa que R36S e outros podem precisar de `mipi-panel.dtbo`. `config/extlinux/extlinux.conf:1–7` usa `/KERNEL`, `FDTDIR`, override de FDT e `FDTOVERLAYS /overlays/mipi-panel.dtbo`. **[Git]** `projects/ROCKNIX/packages/apps/device-switch/scripts/RK3326/device-switch:18–32` altera a seleção FDT em `/flash`, portanto não deve ser executado nesta auditoria.

`projects/ROCKNIX/packages/linux-drivers/generic-dsi/scripts/importpanel.py:26–83,113–179,183–200` extrai painel, delays, formato, lanes, flags, modos e sequência de DTB BSP. Também sintetiza novos modos; **não é uma conversão byte a byte nem um validador**. Não foi executado. Seu `package.mk:5–10,30–35` fixa origem/commit de `overlay_server` e instala outro conversor mais abrangente (`rocknix_dtbo.py`), cujo conteúdo externo não foi analisado. A existência do mecanismo não comprova cobertura de todos os painéis/revisões/clones.

`projects/ROCKNIX/packages/hardware/quirks/devices/Game Console R36S/001-device_config:7–10` define `DEVICE_PLAYBACK_PATH_SPK="HP"`, `DEVICE_PLAYBACK_PATH_HP="SPK"`, GPIO77 e sensor térmico. É evidência de uma particularidade de roteamento, não autorização para aplicar esses valores no driver BSP do dArkOSen.

### E12 — Licenças e redistribuição

- `refs/muos/{frontend,internal,tool}/LICENSE`: texto GPL versão 3. Dependências em `frontend/vendor/*/LICENSE` e bibliotecas externas têm suas próprias licenças.
- `refs/darkosen/LICENSE`: MIT para o projeto; não resolve automaticamente as licenças/proveniência de Linux, U-Boot, DTBs e binários agregados.
- DTS R36S/R3XS do ROCKNIX: cabeçalho `(GPL-2.0+ OR MIT)`; quirk R36S: GPL-2.0; conversor `generic-dsi` é declarado GPL no pacote, exigindo revisão de origem dos arquivos efetivamente aproveitados.
- `refs/rocknix/LICENSE.md:24–31`: software original GPLv2, componentes preservam licenças próprias; branding tem termos separados, inclusive não comercial. Não copiar branding ou uma distribuição inteira como atalho.

Nesta etapa foram transcritos apenas trechos para evidência. Antes de incorporar código, manter avisos/autoria e levantar obrigações por componente, incluindo fontes correspondentes de kernel/U-Boot, módulos, firmware e GPU userspace.

## Riscos prioritários e conclusões delimitadas

1. **Boot e preservação — alto:** bootloader, offsets e DTBs errados podem impedir boot; toda imagem inicial deverá usar cartão separado. O cartão dArkOSen permanece intocado.
2. **ABI e GPU — alto:** loader/glibc/libstdc++ e símbolos, mínimo de kernel da libc, SDL e EGL/GBM/libmali precisam corresponder ao destino. Nem compilação bem-sucedida nem teste em emulador provam execução no aparelho.
3. **Painel — alto:** Panel 0 não equivale à família inteira; DTBs Linux/U-Boot e timings ROCKNIX divergem. Tela preta não prova falha de boot.
4. **Input/energia — alto:** perfil errado pode trocar botões/eixos ou disparar hotkeys/power; não iniciar muinput em modo daemon usando o perfil G350 no sistema atual.
5. **Rootfs e bootstrap — alto:** o boot completo muOS modifica configurações e monta armazenamento; root Btrfs não satisfaz automaticamente as expectativas ext4 dos presets/ferramentas.
6. **Proveniência/reprodutibilidade — alto:** falta fechar receita completa muOS para rootfs/kernel/toolchain; artefatos e ferramentas de atualização não substituem essa receita.

**H:** o caminho de menor risco é provar primeiro ABI de um componente pequeno, depois SDL/GLES e evdev separadamente; usar dArkOSen somente como bancada temporária autorizada. O destino continua sendo firmware muOS AArch64 independente. As fases e critérios estão em [roadmap.md](roadmap.md).
