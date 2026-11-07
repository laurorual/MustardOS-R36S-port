# C16 — comparar controle USB padrão e vendor

## Objetivo e linha de base

28/10/2026: console confirmado no34/C07/IP192.168.15.17:2222/chave fixada,
rootRO/FAT desmontada/taint0/sem sessão ou tokenC12,55 pré-requisitos íntegros.
Original dArkOSen32 preservado; guard seleciona somente o cartão128/Panel0.
O [C13](phase4-network-warm.md) localizou timeout-110 lendo SYS_CFG2/0xfc,
antes de HALMAC identificar o chip. C14/C15 foram negativos e removidos.
Não repetir essas intervenções como se fossem novas.

## Probe fixo de entrada

Código original MIT em port/diagnostics/usb-control-probe.c. Sete pedidos
USBDEVFS_CONTROL fixos, wIndex0, timeout500ms, sem retries:

1. GET_DESCRIPTOR de device18bytes (sem strings/serial).
2. GET_CONFIGURATION1byte.
3. GET_STATUS2bytes.
4. VendorIN0xc0/request5/value0xfc/1byte (identificador do chip).
5. Repetição dos três pedidos padrão após vendor.

São somente pedidosIN. Não há CLI para mudar endereço/pedido, OUT, claim de
interface, detach, reset, reconfiguração, unbind, firmware ou escrita de
registrador/EEPROM. Abertura do usbfs exige O_RDWR e pode executar autoresume
normal do kernel; isso não significa ausência de efeito temporal/PM no ensaio.
Payloads são descartados; saída fixa tem RC, duração e MATCH booleano do valor
esperado (identidade0bda:c820/config1/chip9/statusbits válidos). Não copia MAC,
SSID, PSK, efuse, identificadores USB de string ou dmesg.

O binário valida root/kernel/modelo/taint/namespacePID1, único0bda:c820 em
sysfs e char device189 com minor correspondente a bus/dev. Descritor cached
do fd precisa conferir a identidade; descritor recebido de outra identidade
interrompe o plano antes do vendor. Guard externo preserva CID/root/PARTUUID,
FAT desmontada e ausência do cartão original. Não abrir caminhos escolhidos
pelo operador. Fases CLI são enumeradas, não texto livre.

Fonte consultada: kernel4.4 usb/core/devio.c:835–900,1092–1174 (recipient,
controle, IN/OUT, sem claim de vendor/device) e rtl8821cu/usb_ops_linux.h:22,48
(timeout500/usb_control_msg); usb_ops_linux.c (request/value/index e I/O).
O driver faz também um write posterior em0x4e0 em sua função genérica: esse
write NÃO foi copiado para o probeIN. Portanto observamos a leitura isolada,
não reproduzimos o protocolo completo de I/O do driver. Não atribuir eventual
diferença somente ao userspace sem verificar essa distinção. Nenhum código
GPL foi copiado; usam-se headers UAPI do sysroot e código novo MIT.

## Build e guardas do ensaio

Container existente/SDK Buildroot, -march=armv8-a -mtune=cortex-a35, C11,
PIE/RELRO/NOW, warnings como erro; SDK.config comparada com baseline. ELF64
AArch64, loader/libc já existentes, ABI Linux4.4.0 e símbolosGLIBC até2.38;
loaderQEMU com sysroot da candidata passou. Não instalar libc ou deps no host.
Sete checks AArch64 incluem cinco transportes sintéticos (sucesso, vendor
timeout, timeout geral, identidade errada interrompendo, resposta curta) e
recusas de placa/argumento. Oito fixtures exercitam token, ordem, falhas de
observação sem mascarar resultado do helper original e proibição de consumo
tardio em rootRO. Isso ainda não comprova runtime nativo.

TrialC16 reutiliza o mecanismo dirigido de preimages/rollback da bancada.
Novo muos-c16 contém binário e helperUSB original; wrapper consome token600
once→used/sync na janelaRW inicialC07 e observa antes/depois do helper original.
Observação não adiciona recuperação. Tabela55 conserva todas as entradas,
mudando somente o hash do helperUSB e SHA da tabela na sessão. Binários/perfil
da sessão, kernel/DTB/init/libs/módulos permanecem. C12 não é rearmado.

Baseline34 com dongle funcionando será medida antes de reboot e salva com
sync/readback/unmount em DIAG09/BOOT0034/C16PRE.TXT. Só permitir reboot após
baseline completa e rede preservada. Boot35 mede retained-pre/post, com
relatórios públicos incluídos no REPORT.TXT C07 antes da recuperação física.
Após eventual replug, repetir o plano e comparar. Exigir confirmação física,
preservar o primeiro resultado e remover todo o trial/restaurar os três arquivos
públicos anteriores ao encerrar. Não promover uma mudança de timing a correção
de firmware sem investigação adicional.

## C16/35 — controle padrão também não responde

Stage control.dexdwque, build control-build.3xa7w1ka, wrapper checks.4zs8ipbr.
Baseline34 nativa: sete leituras corretas/MATCH1, rede preservada, relatório
durável C16PRE comparado após35. No35, pre-probe retornou64 sem saída: não
houve medição qualificada ANTES do helper; não atribuir motivo a uma guarda
específica sem instrumentação adicional. Essa limitação permanece explícita.

O post-probe executou após o helper original e ANTES da recuperação física:
GET_DESCRIPTOR, GET_CONFIGURATION e GET_STATUS deram-110; vendor0xfc também;
os três padrões seguintes repetiram-110, cada um em498–500ms. O primeiro
pedido padrão já falhou ANTES da leitura vendor, portanto essa falha geral
não foi causada pela leitura vendor deste plano. Cached descriptors/sysfs
existiam, mas não representam resposta viva do dispositivo.

Usuário precisou reinserir o dongle. Após replug, as mesmas sete transferências
passaram/MATCH1 em0–1ms. REPORT35 com as leituras de falha conferiu com a FAT;
baseline34 sobreviveu idêntica. RootRO/FAT desmontada/taint0 e55 pré-requisitos
do trial passaram. A falha não está limitada à leitura vendor/chip-ID: o canal
de controle EP0 está sem resposta nesse estágio observado. Ainda não demonstra
onde/quando essa condição começa. C16 não é uma recuperação nova.

## C17 — retirar DWC2 ANTES do reboot

C15 retirou/reiniciou o controlador DEPOIS de o dispositivo falhar. A hipótese
temporal restante é que teardown enquanto o periférico funciona evite a
condição retida na transição. Nenhuma nova tentativa de recuperação pós-falha
é adicionada. Código originalMIT pre-shutdown-functions.sh/pre-shutdown.sh,
executor RAM e orquestrador audit-phase4-usb-pre-shutdown.py.

Primeiro, baseline35 completa salva em DIAG09/BOOT0035/C16PRE.TXT. A preparação
não reinicia ou para a rede. Lançamento explícito retira o tokenC16used anterior
para c17.c16-used e arma UMA nova observação C16 no próximo boot, selando root.
Não rearma C12 nem repete seed no mesmo boot. Wrapper/binário C16 não mudam.

Executor exige cartão128/placa/kernel/namespace/rootRO/taint0/55 hashes, sessão
quiescente, BlueZ ausente, único DWC2ff300000 com apenas o composto c820 e
Wi-Fi já vinculado/funcionando. Confere classes/drivers das3interfaces.
Usa lock de manutenção C07, consulta PID/starttime/exe antes da parada de rede;
não inicia/adota infraestrutura C12. Nova leitura completa imediatamente
antes da parada deve ter READ_FAILURES0. Depois network-stop→unbindDWC2→
ausência do controlador→arquivo público FAT→checagem final→pedido normalPID1.

C17PRE.TXT registra os quatro resultados iniciais e intenção ANTES de pedir
PID1, sem afirmar que a syscall/energia ocorreu. Salvo com sync/readback e
desmontagem; falha impede pedido. Aborto tenta bind, restaura os próprios
tokens e tenta rede pelo RNG atual/chave existente. Não há reboot forçado,
GPIO/regulador/registrador arbitrário, driver/kernel/DTB novo ou nova imagem.
Se aborto não recuperar SSH, manter ligado e inspecionar antes de reset.

Nove fixtures validam ordem, cada falha bloqueando PID1 e restauração/tentativa
única, com hardware simulado; shellBusyBox AArch64 conferido. Teste nativo35→36
ainda precisa comparar os controles e confirmar se foi necessário replug.
Ao final, coletar prova pública durável e remover C16/C17/restaurar os três
arquivos públicos anteriores. Nenhuma promoção permanente é automática.

### C17/36 — retirada preventiva comprovada, resultado negativo

Stage pre-shutdown.9jl4ldqy, checks._fhwty1b(9). Baseline35 completa novamente
passou. C17PRE.TXT durável foi relido após36 e comprova baseline/network-stop/
controller-unbind/controller-absentRC0 ANTES da intenção de pedirPID1. Mesmo
assim, controles padrão/vendor post-helper no36 voltaram a dar-110; replug
foi necessário e restaurou os seteMATCH1. Usuário confirmou intervenção.
Não aprovar retirada do DWC2 antes do reboot como correção; agora essa diferença
temporal também tem resultado negativo, não é hipótese pendente.

CleanupC17 retirou o marcador antigo preservado e chamou cleanupC16: USBhelper,
tabela55 e SHA voltaram aos bytes anteriores, muos-c16/tokens removidos,
rootRO/FAT desmontada/taint0/rede pronta. Não houve código permanente de energia
ou mudança de kernel/DTB/driver/bootloader/libs.15checksC16+9C17 passaram.

## C18 — isolar o autoload Bluetooth do composto

Nova evidência de fonte: btusb_probe chama hci_register_dev; hci_core.c:3433
agenda power_on, e hci_power_on:2161 chama hci_dev_do_open sem depender de
bluetoothd. Portanto “BlueZ ausente” não exclui comandos HCI do kernel no
dispositivo composto. Eudev builtin-kmod usa KMOD_PROBE_APPLY_BLACKLIST.
Isso fundamenta testar blacklistbtusb antes do probe, diferente dos resets
anteriores. Não implica que Bluetooth já foi demonstrado como causa.

Única alteração temporária: /etc/modprobe.d/muos-c18-btusb-blacklist.conf,
novo/644/root e hash conferidos, somente blacklistbtusb. Não descarregar BT
do36 em uso; política passa a valer no próximo boot. Verificar módulo ausente
e interfaces0/1 sem btusb, mantendo Wi-Fi/hashes55 originais. Sem módulos ou
firmware novos. Config removida ao finalizar, sem forçar probeBT em rádio ativo.

Dois ciclos têm condições diferentes:36→37 inicia sem btusb no NOVO kernel,
mas36 ainda teve BT;37→38 deve iniciar/terminar com BT ausente. Se37 falhar,
replug antes de38 garante dongle funcional sem BT nos dois lados e evita
atribuir falsamente um estado anterior ao novo autoload. Se37 passar,38 serve
de repetição do candidato. Exigir confirmação física em cada ciclo; não contar
recuperação por replug como sucesso automático. Instalação/parserkmod e coleta
usam o mesmo guard/CID/SSH/rootRO, preservando dArkOSen32. Não copiar logs de
Bluetooth ou identificadores privados; apenas presença de módulo/classes/drivers
e os relatóriosC07 públicos.

### C18/37–38 — dois reboots automáticos aprovados

Stage bt-isolation.khs5p7ey. No37, btusb ausente no relatório inicial e estado
vivo, interfacesBT sem driver e Wi-Fi em rtl8821cu; STATUS0, nenhum recover,
55 pré-requisitos/hashes preservados/rootRO/FAT desmontada/taint0. Usuário
confirmou não retirar o dongle. No38 repetiu com BT ausente antes e depois
do reboot, também automático/sem recover e confirmado pelo usuário. O helper
USB original permanece, inclusive seu caminho de reset/probe; não foi substituído
por outra sequência corretiva. A variável alterada foi a política de autoloadBT.

A política contorna o problema no par Panel0/0bda:c820/kernel atual. A hipótese
de HCI/autoprobe é fundamentada e o efeito da exclusão foi repetido; o pacote
não corrige nem qualifica Bluetooth. Não declarar decodificado o comando interno
que bloqueia EP0 sem uma captura que o demonstre.

## Política estável reproduzível

Código/dados em port/device/rk-r35s-p0/wifi-only, receita opt-in
muos-r35s-wifi-only e fragmento phase4-wifi-only.fragment. Instala somente
etc/modprobe.d/90-muos-r35s-wifi-only.conf e licençaMIT, nenhum init/hook, binário,
módulo, kernel ou configuração privada. O Config.in explica que alias autoload
de TODOS adaptadores btusb fica bloqueado nesta imagem; suporte Bluetooth USB
fica desativado até ser validado. Não generalizar para outras placas/dongles.

Build wifi-policy-build.bxac7so2 verificou a macro real, bytes/modos dos dois
arquivos, Kconfigdefaultoff e optin=y em output separado; SDKconfig permaneceu
byteidêntica. Não foi gerada imagem inteira. Promover exige duas análisesC18
automáticas e confirmações sem replug, hashes/CID/namespace/rootRO/55 e btusb
ausente. Rollback conserva a configuração temporária anterior se ocorrer erro.

Promoção wifi-policy.jdhc3olf passou no38: dois arquivos finais instalados,
arquivo C18 removido, parserkmod exibe uma única blacklist, licença/hash/modos
conferidos, rootRO/FAT desmontada/taint0/55 intactos. Nenhum C16/C17/helper ou
token ficou ativo. Config final permanece instalada; não executar cleanupC18
antigo, que se refere ao trial já promovido. Próximo: conferir reboot38→39 com
o payload final da receita, sem replug, antes de fechar a correção.

### Resultado final — Wi-Fi automático no37/38/39

Boot39 com payload estável: STATUS0/nenhum recovery e usuário confirmou que
não tocou no dongle. InterfacesBluetooth e0 ficam sem driver; interfaceFF
segue em rtl8821cu. Política/licença conferem com a instalação da receita,
todos os55 pré-requisitos/hashes anteriores passaram, rootRO/FAT desmontada/
taint0/brilho80 e contagem selecionada de erros kernel/storage0. Mesmo SSH
fixado/IP192.168.15.17. C07 permanece o default, sem tokenC12/menu permanente.

| Boot | Política no novo kernel | Resultado | Replug |
| --- | --- | --- | --- |
|35 | btusb autoload original | controles padrão/vendor em timeout | sim |
|36 | original, com DWC2 retirado antesPID1 | mesma falha | sim |
|37 | blacklistbtusb temporária | rede/SSH automáticos | não |
|38 | blacklist, BT ausente dos dois lados | rede/SSH automáticos | não |
|39 | payload estável da receita | rede/SSH automáticos | não |

O primeiro coletor final parou apenas numa expressãoawk de I/O mal escapada,
depois de conferir rede/FAT/hashes. Fonte/saídas negativas foram preservadas;
finish-phase4-wifi-verification.py repetiu somente a verificação por leitura,
com a expressão corrigida. A mesma expressão no awkAArch64 contou duas
assinaturas sintéticas corretamente. Nenhum novo reboot ou ajuste do aparelho
foi necessário. Fonte do promoter foi corrigida para usos futuros; a fonte
exata da instalação anterior continua congelada no stage.

**Alteração persistente aprovada na bancada:** somente
/etc/modprobe.d/90-muos-r35s-wifi-only.conf e
/usr/share/licenses/muos-r35s-wifi-only/LICENSE. TrialC18 foi promovido/removido;
C16/C17, seus wrappers/tokens e probes instalados foram removidos e os três
arquivos originais restaurados. Nenhum kernel/DTB/bootloader/partição/módulo/
lib/perfil/ELFC11/init foi trocado. Todos os privados permaneceram no aparelho;
sem exportar payloadUSB/dmesg bruto/seed/PSK/chave privada ou fsck na raiz viva.
Último fsck offline após21;22..39 continuam sem essa verificação.

Pacote opt-in não é um bloqueio absoluto de carga manual: blacklist impede
autoload por alias, não modprobe explícito do administrador. Futuro init deve
respeitar essa política Wi-Fi-only; Bluetooth USB não está validado e não deve
ser ativado por outro serviço. Ensaios abrangem esta combinação Panel0/c820/
kernel4.4.189 e três reboots quentes; boot frio com o pacote final e longa
duração permanecem como verificações futuras. Não foi gerada nova imagem toda.

Provas imutáveis em dist/phase4/usb-control-observation,
usb-pre-shutdown-negative, wifi-bt-isolation e wifi-only-policy, com SHA256SUMS.
**Próximo:** retomar dadosrw com root globalro, defaults apenas uma vez e
preferências de volume/brilho persistentes antes de menu permanente. Não
repetir os mecanismosUSB negativos nem desmontar esta política já qualificada
sem uma nova hipótese/teste de suporteBluetooth. Calibração/escalaUI, bateria,
Power/suspend/fones/conteúdo/licenças completas e longa duração seguem abertos.
