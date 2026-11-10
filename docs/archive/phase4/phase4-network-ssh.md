# Fase 4 — C07: acesso diagnóstico por Wi-Fi e SSH

## Estado corrente — boot39 com política Wi-Fi-only aprovada

Ver [C16–C18](phase4-usb-control.md): blacklistaliasbtusb evitou o bloqueio do
composto;37/38/39 reconectaram automaticamente, sem replug, mesmo SSHfixado.
Config estável e licença são os únicos arquivos novos persistentes; drivers/
kernel/init e55 pré-requisitos preservados. BluetoothUSB permanece desativado
por essa política opt-in. Logs/hipóteses antigos abaixo são históricos.

## Decisão e estado

Após o C06 aprovado, o usuário pediu rede/SSH para reduzir as trocas entre
cartão candidato e dArkOSen. A prioridade passa a ser conectividade
diagnóstica antes dos ajustes reais de volume/brilho. A rodada anterior foi limitada à preparação no host por orçamento de sessão.
Após o reset, a integração foi retomada; o estado atual está ao fim deste
documento e no checkpoint.

O C06 aprovado foi preservado como base do cartão de teste. O dArkOSen está ativo no
cartão original, com o teste no segundo slot e dongle conectado. Estado
exato e identidade das provas no [checkpoint](phase4-resume-checkpoint.md).

## Evidências verificadas

| Item | Fato observado | Limite da evidência |
|---|---|---|
| Dongle no stock | `wlan0`, driver `rtl8821cu`, módulo `8821cu`, USB `0bda:c820`; NetworkManager `100 (connected)`, IPv4 por DHCP | Não comprova associação no kernel próprio |
| Módulo candidato | `extracted/lib/modules/4.4.189-muos-r35s-p4/kernel/drivers/net/wireless/rtl8821cu/8821cu.ko`: vermagic `4.4.189-muos-r35s-p4 SMP mod_unload aarch64`; alias `usb:v0BDApC820d*dc*dsc*dp*icFFiscFFipFFin*` | Não foi carregado nesta rodada; nunca carregar no kernel stock |
| Firmware | `build/phase4/linux-base/drivers/net/wireless/rtl8821cu/include/autoconf.h:72`: `#define CONFIG_EMBEDDED_FWIMG` | Indica imagem embutida; logs do primeiro boot ainda devem confirmar inicialização |
| Blueprint atual | `build/phase4/linux-diagnostic/frontend-navigation-level.ed62uz58/extracted` não contém wpa_supplicant/Dropbear | Ferramentas precisam ser compiladas para seu próprio ABI/rootfs |
| DHCP | BusyBox existente tem `CONFIG_IP=y`, `CONFIG_UDHCPC=y` | Preparar hook próprio com estado em `/run`; não assumir que o default serve |
| muOS upstream | `refs/muos/internal/script/init/async/S02network.sh` lê perfil por GET_VAR, seleciona wpa_supplicant por arquitetura/driver e usa dhcpcd | A receita nativa será referência para integração final; não habilitar seu conjunto completo de serviços no diagnóstico |

O alias/vermagic foram consultados com modinfo no host. O inventário SSH
não leu SSID, senha ou conteúdo de perfis. As fontes em refs permaneceram
somente leitura.

## Ferramentas e ABI

O controlador [build-phase4-network-tools.sh](../../port/scripts/build-phase4-network-tools.sh)
usa o Buildroot já fixado em `4f924fd52841608d68ac3dcb83fccee8b8c90316`
e a imagem de container registrada em `build/phase4/rootfs-container.iid`.
Reutiliza o SDK AArch64/glibc da candidata, com builds de pacotes específicos;
não instala dependências no Bazzite nem executa `make all`.

Receitas inspecionadas em `build/phase4/buildroot/package/`:

- `dropbear/dropbear.mk`: versão2026.93, MIT/BSD-2-Clause/domínio público;
  modo pequeno também declara Unlicense/WTFPL das bibliotecas incluídas.
  `LICENSE`, `libtommath/LICENSE` e `libtomcrypt/LICENSE` devem acompanhar
  a prova de compilação. Sem cliente, algoritmos legados, wtmp ou lastlog;
  sem reverse DNS. Autenticação por senha será desabilitada na execução.
- `wpa_supplicant/wpa_supplicant.mk`: versão2.12, BSD-3-Clause, termos em
  `README`. Compilar nl80211 e fallback wext, interface de controle e
  wpa_cli; sem novo serviço D-Bus, WPS ou modo AP.
- `libnl/libnl.mk`: versão3.11.0, LGPL-2.1+, `COPYING`.
- `libxcrypt/libxcrypt.mk`: versão4.4.38, LGPL-2.1+, `LICENSING`/`COPYING.LIB`;
  dependência selecionada pelo Dropbear em glibc, mesmo com senha bloqueada
  no diagnóstico.

O SDK/output existente é mutável e compartilhado com foundation. O
controlador recusa outro container phase4 em execução, usa flock entre
suas próprias invocações, salva a configuração original e a restaura no
fim de cada estágio. **Não executar outro controlador do SDK em paralelo**:
os controladores históricos não compartilham esse flock. Configuração e
logs ficam em `build/phase4/network-tools/`. Pacotes novos podem adicionar
arquivos ao target/staging mutável; isso não altera imagens/provas congeladas.
Não usar uma imagem regenerada desse target como atualização do cartão.
Em caso de interrupção externa, conferir baseline/config e container antes
de retomar; nenhum passo do controlador acessa dispositivo.

Após compilar, auditar ELF/loader/QEMU contra o blueprint C06 com somente
as novas dependências necessárias. Conferir bibliotecas existentes por
hash antes de reutilizá-las. `--help`/loader não equivalem a testar Wi-Fi,
SSH, criptografia ou comportamento no kernel4.4. Não copiar binários Debian.

## Menor primeiro teste executável

O primeiro boot C07 será **somente rede/SSH**, sem áudio ou frontend.
Manter bootstrap/guardas de kernel, Panel0, CID/partição e ausência do
cartão original; adaptar explicitamente a guarda que hoje recusa o dongle.
Preservar o runner C06 para um futuro ensaio remoto separado.

1. Iniciar RNG nativo e aguardar prontidão antes de consumidores/chaves;
   depois coldplug e módulo8821cu. Conferir interface e alias reais.
2. Provisionar a rede **localmente no aparelho**, a partir do perfil ativo
   do stock, sem imprimir SSID/PSK, transferir ao host ou incluir credenciais
   no blueprint, manifesto ou dist. Validar tipo de autenticação antes de
   definir o conversor; ele ainda não foi implementado. Não exportar seed.
3. wpa_supplicant usa cópia privada em `/run`, `update_config=0`; logs de
   diagnóstico públicos devem excluir SSID, PSK e informações pessoais.
   Logs privados não entram nas coletas/artefatos. DHCP IPv4 por udhcpc com
   hook próprio; não assumir que o endereço anterior será reutilizado.
4. Dropbear em porta2222, apenas chave pública de cliente dedicada. Chave
   privada cliente permanece local ao host, fora de artefatos; chave de
   host é gerada no aparelho após RNG pronto e persiste somente no cartão.
   Confirmar fingerprint público pela tela antes de fixar known_hosts
   dedicado. Não reutilizar senha padrão ark nem alterar SSH global do host.
5. Exibir IP/porta/fingerprint e status na tela. Manter raiz read-only após
   provisionamento, processos/pids/logs em `/run` e nenhum daemon mantendo
   arquivos graváveis na raiz. Não ligar automaticamente os serviços muOS
   de rede/discovery/web, nem o init S50dropbear genérico da Buildroot.
6. Pela nova conexão: confirmar kernel/modelo/root/taint, executar comando
   simples e testar pequena transferência via SSH. Não requer SFTP.
   Só então planejar start/stop supervisionado do menu preservando a rede.

Critério: Wi-Fi associado, IPv4 obtido, fingerprint conferido e comando
SSH por chave no kernel/rootfs próprios, com raiz read-only e sem depender
do dArkOSen. Um sucesso não aprova reconexão, hotplug ou estabilidade longa.
Antes desse boot ainda faltam serviço, provisionador, instalação guardada,
auditoria de cleanup/falhas e captura de logs sem segredos.

## Riscos e pendências

Firmware embutido/driver Realtek continuam sujeitos a revisão de termos;
não inferir licença do firmware a partir da licença do módulo. Manter uso
privado e incluir pendências na consolidação final solicitada pelo usuário.
Atualizar o inventário de licenças quando os fontes dos novos pacotes forem
extraídos. Sem contato com fornecedores nesta rodada.

Kernel4.4 pode expor diferenças nl80211/wext, rfkill e USB; isso é hipótese
até o primeiro boot com dongle. Falha de conexão deve terminar em tela
diagnóstica e logs preserváveis, sem tentativa de reflash/recovery. O
cartão original continua sendo a recuperação independente. Provisionamento
de segredos e geração de chaves não devem entrar em backup de instalação.

## Retomada: modo disco virtual confirmado e C07 instalado

O usuário alertou sobre o modo CD-ROM antes da integração. A inspeção
somente leitura no stock confirmou pacotes usb-modeswitch2.6.1 e dados20191128;
`/etc/udev/rules.d/40-usb_modeswitch.rules` substitui a regra genérica com:

```text
ATTR{idVendor}=="0bda", ATTR{idProduct}=="1a2b", RUN+="/usr/sbin/usb_modeswitch -K -v 0bda -p 1a2b"
```

Dmesg mostra1a2b seguido de c820. O configPack genérico contém entrada
D-Link1a2b com TargetVendor2001/TargetProduct331d: esses IDs de destino
**não** correspondem a este exemplar. Reutilizamos a operação StandardEject
comprovada pela regra local, exigindo depois c820; não a identidade D-Link.
A conexão Wi-Fi stock não foi ejetada/interrompida nessa inspeção.

C07 acrescentou usb_modeswitch2.6.1 (GPL2+/BSD2) e libusb1.0.30 (LGPL2.1+)
compilados pelo mesmo SDK. Somente executável/lib necessários entram no
payload; sem dispatcher, regras genéricas ou jimtcl no runtime. Licenças
foram retidas no pacote e em `/usr/share/muos-diagnostic/c07-licenses.txt`.

`network-diagnostic/usb-mode.sh` recusa múltiplos dongles, ID desconhecido ou
interface inicial sem classe08. Se já c820, não ejeta. Se1a2b, executa -K
com bus/dev exatos e aguarda c820 no mesmo caminho físico. Só então inicia
8821cu. Não seleciona dispositivo por `/dev/sdX` e não toca partições SD.
Onze fixtures dos hooks reais passaram em container sem hardware, com sysfs
falso e comandos stub. São testes de guardas/transições, não de USB real.

Build, dependências transitivas e auditoria ELF/loader/QEMU passaram;
libnl-genl retinha RPATH de compilação por não rodarmos finalização global.
A auditoria recusou a primeira cópia e a versão final remove esse RPATH
somente nas novas cópias. Bibliotecas existentes coincidem por hash;
configuração foundation foi restaurada. Nada de binários Debian foi importado.

Blueprint host **sem credenciais/seed**: `network.n09y22sw`; ferramentas
`network-tools/audit.epuqygvx`; fixtures `network-tools/hooks.wvah_zf5`.
Prova `dist/phase4/network-preboot/`. Dezoito arquivos instalados somente
em p2 do cartão autorizado, com preimages/identidades, rollback, releitura
por hash e fsck0. Kernel/DTB/U-Boot/tabela preservados. O provisionador
converte o perfil ativo WPA-PSK localmente para arquivo root600 em diretório
root700; não registra valores/hash/backups desse conteúdo. Seed só teve
metadados do diretório verificados. Instalador remoto removido; stock saudável.

Primeiro boot físico ainda pendente. A rede ficará ativa com raiz read-only,
logs privados em `/run` e relatório público DIAG09 sem logs dos daemons ou
conteúdo das credenciais. Sem áudio/frontend, DNS ou rota default. A tela
mostra IP/porta2222/root e fingerprint SHA256 para pinagem pelo cliente.
O primeiro teste ainda deve comprovar ejeção, associação, DHCP, autenticação
por chave e comando remoto. Não confundir processos ativos com esses sucessos.

## Primeiro boot: falha, raiz read-only preservada

Usuário confirmou `muOS C07: STOPPED / Network test failed; DIAG09 saved /
ROOT_RO=1`. Viu também enumeração0bda:1a2b/USB-storage/CD-ROM. Ainda não
há evidência suficiente para atribuir a falha à ejeção: o helper faz outras
verificações antes dela. Coleta DIAG09 pelo stock foi solicitada; não repetir
nem inferir causa antes dos registros. O coletor agora reconhece C07/DIAG09.

Preferência do usuário: salvar detalhes no relatório e solicitar apenas a
mensagem curta na tela. Novos ensaios devem reduzir transcrição manual e
persistir diagnóstico público suficiente, sem credenciais, chaves privadas,
SSID ou logs privados dos daemons. A pinagem SSH poderá usar um fingerprint
público obtido pela conexão stock confiável se a chave já tiver sido gerada,
evitar também a transcrição manual longa de fingerprint nesse caso.

## C07r1 — prazo inválido identificado e correção instalada

Coleta `network.n09y22sw/boot1`: status1/rootro1/taint0, sem network.log,
interface, associação, endereço ou fingerprint; fsck0 e saúde stock passaram.
O runner enviava200 a muos-run-bounded; `port/utils/muos-run-bounded.c:26`
recusa valores acima de120 e retorna125 antes de fork/exec. A reprodução
com o mesmo ELF AArch64 confirmou200→125 e120→0. R0 não registrava RC;
portanto125 é reprodução/derivação do código, não leitura direta do aparelho.
Esse erro bloqueava necessariamente a chamada; o teste ainda não avalia
sucesso/falha da ejeção real ou do rádio. Host key ainda ausente por metadados.

R1 separa USB75s e conexão120s (RNG90/udev45/stop30), sem mudar o executor
nem binários. Acrescenta resultados por etapa/subetapa, logs textuais do RNG,
arquivos de tentativa BOOTnnnn e mensagens finais curtas. Não coleta chaves,
SSID, PSK, logs privados dos daemons ou dmesg Wi-Fi. Printk3 oculta mensagens
informativas na tela. A montagem FAT continua desmontada antes do estado final.

Blueprint sem segredos `network-deadline.6qfz33xd`. Quatorze checks dos hooks,
limites e executor real, QEMU shell/ext4/fsck passaram. Instalador ganhou
caminho r1 estreito para somente dois scripts; não reprovisiona nem lê/hash/copia
credenciais ou seed, só verifica metadados. SHA de todos os outros arquivos
públicos esperados foi conferido. Instalação, releitura, fsck0 e saúde stock
passaram; temporários removidos. Provas negativas, preboot e instalação
estão separadas em dist/phase4. Teste físico r1 pendente.

## BOOT0018 — Wi-Fi/SSH nativos aprovados

Usuário confirmou READY e comparou o fingerprint público apresentado pelo
host com o da tela, apenas respondendo sim. Chave fixada em known_hosts
exclusivo; autenticação root por chave dedicada na porta2222 passou.
Consulta confirmou kernel4.4.189-muos-r35s-p4/AArch64/Panel0/PID1BusyBox,
CID do cartão de teste, raiz realmmcblk0p2/ext4ro, taint0 e rede ativa.
Transferência de28bytes em /run voltou idêntica e o arquivo foi removido.

Relatório DIAG09/BOOT0018: todos os cinco estágiosRC0; USB1a2b→c820 por
StandardEject observado, módulo8821cu, wlan0/COMPLETED/DHCP192.168.15.17.
RNG persistido pronto8015ms, refresh conservador nativo e parada completos.
Report FAT arquivado foi relido em montagemro e comparado com /run; FAT
novamente desmontado. Snapshot final em uptime168,18s: raiz ro, taint0,
serviço vivo e zero assinaturas fatais/storage selecionadas no dmesg.
A varredura retorna somente contagem, sem exportar dmesg/SSID/logs privados.

Prova congelada `dist/phase4/network-boot/`; análise/coleta em
`network-deadline.6qfz33xd/boot1`. A candidata permanece ligada para iteração
remota, original32 guardado. Não houve retorno stock nem fsck offline depois
deste boot; fsck antes do boot passou. Nenhuma aprovação de longa duração,
reconexão/hotplug/reboot, função Bluetooth ou UI com rede. Não recolher as
chaves privadas, credenciais, seed ou raiz viva como “backup de diagnóstico”.
Próximo incremento deve compartilhar os serviços ativos ao integrar o C06,
evitar recarregar seed salvo no mesmo boot ou disputar lifecycle de udev.

## BOOT0019 — reboot alcançou Linux, interface não encontrada

Após C08 aprovado, reboot normal solicitado de rootro chegou ao C07/BOOT0019.
Relatório coletado no stock: entropy-start/udev/usb-mode/entropy-stopRC0;
networkRC1 em NETWORK_STEP=driver, “interface missing”. Módulo8821cuLive;
o seletor por parent/driver/module não encontrou netdev correspondente.
O relatório não enumera todos os netdevs, portanto não prova sozinho que
não havia qualquer interface. Chave pública permaneceu idêntica e RNG
persistido/refresh nativo passaram (pronto7013ms). Rootro/taint0, fsck offline0,
Image/serviços stock e cinco contadores Btrfs0 passaram. Esse fsck também
cobre os writes do ensaio C08 anterior; a prova C08 foi congelada antes dele.

Diferença observada: USB começou como c820 e a versãor1 pulou a ejeção;
BOOT0018 tinha começado1a2b. Estado interno retido/ordem de probe é hipótese,
não causa demonstrada. Interface física no stock é1-1:1.2 FF/FF/FF/rtl8821cu;
as interfaces0/1 são BluetoothE0/01/01/btusb. Regra de net naming não foi
identificada no blueprint. O módulo tem rtw_switch_usb_mode padrão0.

## C07r2 — workaround direcionado, testes nativos pendentes

Três scripts atualizados;20 checks, QEMU shell/ext4/fsck/identidades e saúde
stock passaram. No boot já c820 e antes de C07ready, usb_modeswitch -R é
limitado ao VID/PID e bus/device exatos. A ferramenta2.6.1 tem resetUSBvoid
que pode terminar0 após erro; exigimos “Device was reset” no log privado.
Ela usa libusb_reset_device: reset de porta USB com tentativa de restaurar
configuração/altsetting, podendo exigir redescoberta; não é power cycle nem
comando de EEPROM. [Documentação libusb](https://libusb.sourceforge.io/api-1.0/group__libusb__dev.html).

Depois, aguarda o dispositivo conhecido, ejeta se voltou1a2b e aguarda udev.
Como reset pode não repetir probe anteriormente recusado, carrega8821cu e
pede drivers_probe somente para interface FF/FF/FF sem driver, no mesmo
c820. O kernel4.4 em drivers/base/bus.c:257–270,776–788 procura pelo nome
e chama device_attach só se não existe driver. Não desassocia interfaces
vinculadas, não escreve em dispositivos de bloco/hubs/EEPROM. O reset é do
dongle composto inteiro; Bluetooth não é validado por este diagnóstico.

A transição fria1a2b→c820 mantém o método anterior. Modo já ativo C07ready
recusa novo reset. Falhas futuras de seleção registram classes/drivers USB
e módulos de netdev, sem MAC/SSID/PSK ou logs privados exportados. Limite
USB120 mantém o contrato1..120 do executor; rede120 inalterado.

Blueprint sem segredos network-reprobe.g4tsxr3s. Instalação guardada altera
somente usb-mode/network/run na p2 autorizada; preserva privados por metadados.
Provas BOOT0019/preboot/instalação separadas. Ainda faltam boot frioR2 e
reboot com c820retido para avaliar o workaround. Não atribuir causalidade
isolada a reset ou reprobe mesmo se a combinação resolver.


## BOOT0020/21 — reset/reprobe insuficientes; C07r3 preparado

BOOT0020 frioR2 passou (1a2b→c820). Reboot normal BOOT0021: reset confirmou
sucesso e drivers_probe de1-1:1.2 retornou0, porém a interfaceFF permaneceu
DRIVER=none e apenaslo existia. NetworkRC1 antes da associação; etapas RNG,
udev,USB e parada do RNGRC0. Rootro/taint0, chave preservada, prontidão7514ms.
Fsck offline0 e saúde stock passaram. Não foi timeout nem sucesso de reboot.
O retorno0 de drivers_probe não demonstra vínculo de driver; resultado
negativo congelado em `network-reprobe-reboot-failure/`.

R3 adiciona contagens de classes conhecidas de falha do driver, sem exportar
linhas brutas do dmesg, MAC/SSID ou logs privados. Não modifica o driver.
Acrescenta recuperação por uma retirada/reinserção física após falha USB/rede:
exige rootro, RNG pronto por consulta não bloqueante, seedrng já parado e
chave host existente; guarda CID/root recusa o cartão original. Uma ausência
real de pelo menos1s deve preceder a nova presença. Prazos90s para retirar,
120s para recolocar; depois USB/rede com limites120s cada. Só uma tentativa,
sem reset contínuo ou alteração de seed/chave. Falha original BOOTnnnn e
RESULT permanecem; RECOVER.TXT registra resultado independente. READY recuperado
não será contado como reboot automático aprovado. Falha de recuperação ainda
exige retorno stock para coleta. Um sucesso permite observar o driver via SSH.

Blueprint sem segredos `network-recovery.zz7sq2ve`; alteração de três scripts,
20 checks anteriores +13 de recuperação/falhas/filtragem, shell QEMU e ext4/fsck
passaram. Instaladorr3 mantém preimages/rollback e privados por metadados;
coletor aceita RECOVER.TXT opcional nos arquivos C07. Instalação e teste físico
pendentes. Workaround físico é provisório; a causa do warm boot segue aberta.


## C07r3 — recuperação física aprovada no BOOT0024

BOOT0022/23 frios passaram,23 autenticado por chave e51 hashes públicos
conferidos. Reboot24 repetiu interfaceFF sem driver/lo apenas, apesar do
reset/reprobeRC0. Counters de falha deram0, porém loglevel3 suprime RTW_INFO:
ausência de contagens não exclui erro de inicialização do driver. Kernel
source `rtl8821cu/Makefile:84–87` e `include/rtw_debug.h:136–142` sustentam
esse limite; leitura nativa do parâmetro confirmou3.

Usuário retirou/reinseriu o dongle uma vez e confirmou online; SSH por chave
com mesmo fingerprint passou. RECOVER.TXT mostra ausência física,1a2b→c820,
RNG atual pronto, DHCP/SSH e RECOVERY_RC0. OriginalREPORT/RESULT1 foi
preservado e comparado byte a byte com FAT; recuperação independente foi
comparada também. Rootro/taint0/FAT desmontado e51 hashes íntegros. Prova
`dist/phase4/network-physical-recovery/`. Sem fsck offline após22..24.
Registros de desaparecimento sysfs durante reenumeração não impediram êxito;
leitura atômica/limpeza dessas mensagens ainda é melhoria cosmética pendente.

Próximo teste isolado (RAM, sem init persistente): parar rede, remover8821cu
sem força e depois reboot normal. Fonte `os_dep/linux/usb_intf.c:49–84` usa
rtw_hal_deinit no callbackshutdown; `:1520–1657` inclui parada de threads,
rtw_usb_primary_adapter_deinit,usb_deregister e platform_wifi_power_off no
caminho de remoção/moduleexit. Isso motiva o teste, sem provar causalidade.
Executor próprio sob network-driver-diagnostic, sete fixtures de ordem,
aborto/restauração e guardas; QEMU BusyBox e pré-requisitos nativos passaram.
Registra PREBOOT.TXT público antes de reiniciar e desmonta FAT, sem tocar
seed/credenciais/chaves/rootfs. Se a tentativa falhar, r3 continua disponível.
Blueprint `network-unload.vq4y1x6v`, prova network-unload-preflight; resultado
nativo pendente. Código temporário desaparecerá no reboot.


## Resultado do unload e continuidade da bancada

PREBOOT.TXT do24 confirma networkstop0 e remoção8821cu antes de reboot
normal. BOOT0025 falhou de novo em interface ausente; user reconectou o dongle
e a recuperação voltou por SSH com a chave fixada. Rootro/taint0/FAT e51hashes
passaram. Prova network-unload-reboot-failure. Hipótese de unload insuficiente;
nenhum novo shutdown persistente adotado. Não inferir que reset/reprobe/unload
resolveram warmboot. Causa aberta e recuperação física validada em24/25.

Nessa mesma sessão25, C09 exercitou helpers/hotkeys/áudio/menu/SSH e cleanup
sem trocar cartões ([C09](phase4-network-controls.md)). Candidata segue ligada
headless com SSH; original32 guardado. Não houve fsck offline depois22..25.
