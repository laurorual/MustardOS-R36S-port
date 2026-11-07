# C13 — localizar a falha do dongle após reboot

## Atualização — Wi-Fi automático no37/38/39

O [C18/pacoteWi-Fi-only](phase4-usb-control.md) resolveu os reboots observados
bloqueando autoloadbtusb: três reboots sem replug confirmados, política estável
instalada e receita opt-in verificada. Bluetooth USB segue desativado. C13–C17
abaixo são diagnósticos/negativos preservados; não repetir esses mecanismos.
ÚltimoestadoC07/39/rootRO/FAT desmontada/taint0/55 hashes/chavefixada confere.
Próximo é persistência de preferências, mantendo a política estável.

## Linha de base e pergunta

28/10/2026: boot31/C07 confirmado por SSH fixado em192.168.15.17:2222,
rootRO/FAT desmontada/taint0, sem sessão ou tokenC12. Original dArkOSen32
preservado; guard exige cartão128 e Panel0. O dongle0bda:c820 está em1-1,
configuração1, três interfaces: Bluetooth0/1 em btusb e Wi-Fi2 em rtl8821cu.
USB runtime active/controlon; rtw_enusbss0/rtw_power_mgnt0/rtw_low_power0.
Não há evidência para atribuir a falha atual a autosuspend.

Reset USB, reprobe, unload8821cu e stop de rede/udev já falharam; nenhum é
repetido como hipótese corretiva. A causa ainda não foi localizada porque
RTW_INFO está suprimido por rtw_drv_log_level3. É o defeito de observação
identificado nos boots24/25, não uma nova constatação de ausência de driver.

## Incremento mínimo: observar a primeira falha com log4

Única mudança temporária no cartão: arquivo novo e previamente ausente
`/etc/modprobe.d/muos-c13-warm-probe.conf`, com
`options 8821cu rtw_drv_log_level=4`. kmod nativo foi confirmado. Instalação
por arquivo temporário/rename, hash/modo e modprobe-c conferidos, rootRO depois.
Não troca driver, firmware, kernel, DTB, init, helperUSB/rede ou hashes aprovados.
Nenhum tokenC12 é armado e nenhuma sessão/menu é repetida. Boot C07 normal
executa a mesma tentativa conhecida, agora com visibilidade antes do probe.

Driver pode registrar identificadores privados no ring buffer local. **Nenhum
dmesg bruto é exportado ou salvo pelo coletor.** `driver-events.awk` produz
somente18 rótulos fixos, contagens e primeiro/último tempo numérico. Ring buffer
não é limpo. Relatórios C07/recuperação já públicos são coletados separadamente.
Após coleta, remover somente a configuração com hash esperado e restaurar
o parâmetro runtime3. C07 físico continua como recuperação; não reimportar seed
ou gerar chave. Falha do SSH exige preservar aparelho ligado e verificar tela.

Fontes consultadas por leitura: rtl8821cu/Makefile:84–87 e rtw_debug.h:136–142
(log3 suprime INFO); usb_intf.c:1232–1513 (HAL ops, chip info, software/netdev);
rtl8821cu_ops.c:267–280 e rtl8821c_ops.c:466–545 (HALMAC/efuse). Código novo é
original MIT. Não foi copiado subsistema das refs. Regra dArkOSen de ejeção
já fundamenta o helper existente; a referência ROCKNIX de dwc2/PM é de outra
stack e não prova pertinência a esta falha de probe. Não aplicar esse patch.

`bConfigurationValue` do kernel4.4 chama usb_set_configuration, que é uma
operação diferente do reset anterior e poderia testar reconfiguração completa
do composto. É somente hipótese futura, ainda não executada. Evitar escrever
em reguladores/GPIO ou cortar VBUS sem comprovar alimentação e consumidores:
boost está enabled e otg_switch disabled com dongle funcionando, portanto esses
nomes não bastam para assumir controle seguro da porta.

## Validação

Cinco casos no awk BusyBox AArch64 real via QEMU verificam formato, contagens,
tempos, ausência de identificadores privados e separação HALMAC/efuse. Isso
valida somente o filtro, não driver/radio/reboot. Orquestrador mantém fontes,
hashes baseline e scripts exatos no stage; cada ação é explícita. `reboot-attempted`
impede repetir o pedido no mesmo stage. Instalação não reinicia o aparelho.

Teste físico planejado:31→32, uma reconexão do dongle se C07 pedir, coleta
classificada e remoção de config/log4. A repetição é justificada pela nova
observabilidade; não conta como aprovação de reset/reprobe nem de correção.
Registrar o resultado abaixo antes de propor outra intervenção.

## C13/boot32 — falha localizada; diagnóstico removido

Stage probe.nsbst7kz, filtro checks.z0w36qcj. Usuário reconectou o dongle;
nível4 foi confirmado no módulo. Os eventos mostram HALMAC init/primary failed
duas vezes em16,866s e21,346s, antes de chip_version/chip_info da recuperação
física em42,060/42,480s. Coleta numérica adicional, sem linhas brutas, confirmou:
dez retornos USB-110 ao ler o identificador em0xfc, HALMAC status54 duas vezes
e duas ocorrências de Chip id undefined. Buffer começa em0s: esses eventos
iniciais não foram simplesmente perdidos por rotação do ring.

halmac_type.h define54/0x36 como HALMAC_RET_CHIP_NOT_SUPPORT; halmac_api.c
get_chip_info lê SYS_CFG2/0xfc e retorna esse código quando o byte não identifica
um chip conhecido. Aqui a leitura sofre timeout USB; o código NÃO demonstra
hardware incompatível. A identificação falha antes de efuse/associação/DHCP.
O filtro anterior de I/O não capturava a mensagem `reg..., usb read...fail`,
o que explica a inadequação dos antigos contadores0 como prova de ausência.

Configuração temporária removida após coleta, módulo voltou a nível3; todos
os hashes55/baseline, rede, rootRO/FAT desmontada/taint0 passaram. Nenhum
script/kernel/driver/init foi alterado pelo C13. Scripts e provas no stage.

## C14 — candidato: desconfigurar/reconfigurar o composto

Hipótese diferente: USB reset preserva/restaura configuração e altsetting;
SET_CONFIGURATION0→1 libera/recria as interfaces do dongle e pode recuperar
seu atendimento a comandos vendor após o warm boot. Não implica ciclo de
alimentação. O kernel4.4 sysfs.c:82–94 chama usb_set_configuration; message.c
libera interfaces e reconstrói a configuração. Não foi necessário copiar código
upstream. Auto-resume já é feito por usb_probe_interface antes do callback:
isso reduz a justificativa para um patch especulativo de PM no8821cu.

Código originalMIT em reconfigure-functions.sh/reconfigure.sh/usb-trial.sh.
Guards: cartão128/Panel0/kernel próprios/taint0/mesmo namespacePID1, C07,
nenhuma rede/UI/BlueZ em uso, único0bda:c820 com uma configuração/3interfaces,
Bluetooth somentebtusb e interfaceFF sem driver. Não aceita outros dispositivos,
interfaces de storage ou Wi-Fi já vinculado. Cada write tem prazo10/30s;
restauração de configuração1 ocorre após falha/timeout/interrupção. Sem força,
GPIO/regulador, escrita de registrador/EEPROM ou loop de reset.

Trial usa tokenMUOS-C14-ONCE root600 consumido/sync antes da ação, somente
na janelaRW inicial C07. Sem token, chama exclusivamente o helper original.
O helperUSB original executa primeiro para preservar a evidência conhecida;
somente depois entra a nova intervenção. Não se atribuirá sucesso ao reset
anterior. DefaultC12/allow_power0 e recuperação física C07 permanecem.

Instalação: diretório novo muos-c14 com originais/helpers e wrapper no caminho
USB existente; pré-requisitos mantêm55 entradas e mudam SOMENTE o hash esperado
desse helper, com SHA256SUMS da sessão regenerado. Código/binários/perfil da
sessão não mudam. Bytes públicos anteriores são preservados para rollback/
cleanup. Teste passa por rootRO e autenticação SSH antes de aprovação. Após
coleta, restaurar os três arquivos públicos anteriores e remover helper/token
de ensaio; promoção permanente exige etapa separada e novo ensaio da integração.

20 fixtures host cobrem seleção/recusa, falhas0/1/readiness com restauração,
tentativa única e wrapper/token reais com callbacks simulados. Shell dos scripts
é analisado pelo BusyBox AArch64. Isso não substitui o ensaio físico32→33.
Neste boot, usuário deve manter o dongle conectado; replug apenas se a tela
solicitar fallback, para distinguir recuperação automática de física.

### C14/boot33 — negativo e restaurado

Stage reconfigure.0y8luql1, checks.xacs606s. Token consumido; configuração0RC0,
configuração1RC0, ausência de driver/netdev e restore1RC0 foram coletados.
Usuário precisou reconectar fisicamente, e C07 recuperou SSH. Não aprovar esse
workaround: retornar0 de SET_CONFIGURATION não equivale a recuperar vendor I/O.
Cleanup restaurou helperUSB, tabela55 e SHA anteriores, removeu muos-c14/token,
conferiu todos os hashes e rootRO/FAT desmontada/taint0/rede pronta. Log3.

## C15 — hipótese de ciclo completo do controlador DWC2

Topologia nativa: só usb1 em /sys/devices/platform/ff300000.usb, driverdwc2;
dongle é o único filho físico. Compatible px30-usb/rk3066-usb/snps,dwc2. Não
é EHCI. platform.c do kernel próprio: remove:465–484 remove HCD/gadget,
desabilita recursos/PHY e assert de reset opcional; shutdown:499–504 só
disable_irq. probe reabilita recursos e executa core reset. Isso fundamenta
um teste novo do lifecycle completo do controlador, diferente de reset do
dongle/SET_CONFIGURATION ou unload8821cu. Não demonstra ainda causa no DWC2.

Trial separado com tokenC15, sem executar C14. Guarda reaproveita seleção do
composto, exige único root hub/exclusivamente esse dongle e controlador exato
ff300000.usb vinculado a dwc2. Recusa controlador/barramento/dispositivo adicional,
rede/BlueZ/UI ativos ou interface Wi-Fi já vinculada. Unbind20s, bind30s,
espera de nova enumeração/readiness; números de bus podem mudar. Se retornou
1a2b, usa a ejeção original; se c820, não repete o reset do helper sobre uma
interface possivelmente já recuperada. Em falha, tenta restaurar bind uma vez.
Não manipula GPIO/reguladores/registradores diretamente nem flash; usa os
callbacks existentes do kernel para teardown/reinicialização dos recursos.

Método de instalação/guardas/hashes/rollback/cleanup é o mesmo do trialC14,
com muos-c15/token próprios e fonte congelada separada.12 fixtures adicionais
testam exclusividade da topologia, ordem, tentativa única e restauração
após falha de unbind/bind/readiness. Kernel/driver/DTB/init continuam intactos.
Se nem o controlador voltar, preservar energia para diagnóstico antes de
qualquer recuperação física adicional. Aprovação exige SSH e confirmação
explícita do usuário de que não retirou o dongle.

### C15/boot34 — negativo e restaurado

Stage controller.i16vj5bd, checks.q0_yi8y3. Token consumido, unbindRC0 e bindRC0
com ausência de driver/netdev; restore-bindRC0. Usuário precisou replug físico.
C07 recuperou SSH. O ciclo do controlador ocorreu; não foi apenas preparação
host. Ainda assim NÃO resolveu o problema. Não repetir como hipótese nova.

Cleanup restaurou todos os bytes públicos anteriores: helperUSB, tabela55 e
SHA da sessão. muos-c15/c15.once/c15.used foram removidos; C14 também já tinha
sido removido. ConfigC13 ausente/log3, C12 sem token/allow_power0. Verificação
final por SSH no34/C07/IP192.168.15.17 confirmou rootRO/FAT desmontada/taint0,
brilho80,55 pré-requisitos, quiescência/rede e zero assinaturas selecionadas de
erro kernel/storage. DWC2 reset-timeouts0 na classificação escolhida: não há
base para aplicar o patch ROCKNIX de soft reset/PM apenas pela palavra DWC2.
Nenhum cartão original foi tocado, nenhuma nova imagem/partição/kernel/DTB/
biblioteca/módulo foi gravado e nenhum fsck foi feito na raiz viva. Último fsck
offline continua após21;22..34 sem essa verificação.

## Resultado e próximo recorte registrados apósC15 (superados peloC18)

37 checks host (5 filtroAArch64+20 reconfiguração/token+12 controlador), shell
BusyBox AArch64 e três ensaios nativos foram executados. C13 aprovou a nova
observabilidade; C14/C15 são resultados NEGATIVOS, não correções promovidas.
Provas públicas imutáveis com SHA256SUMS em dist/phase4/network-warm-probe,
network-reconfigure-trial e network-controller-trial, com fontes/ações exatas,
confirmações do usuário, relatórios antes/depois e comprovantes de cleanup.
Não há dmesg bruto, MAC/SSID/PSK ou seed/chave privada nesses artefatos.

**A recuperação automática continua aberta.** Evidência localizada: leitura
vendor de SYS_CFG2/0xfc retorna USB-110 antes da identificação do chip; reset,
reprobe, unload, parada ordenada, SET_CONFIGURATION e ciclo DWC2 depois da falha
não a recuperaram. Replug faz voltar1a2b→c820 e inicializa normalmente. Isso
é compatível com estado retido do periférico/caminho de controle, mas não prova
onde esse estado se corrompe nem se uma intervenção no shutdown o evitaria.

Próximo recorte sugerido: auditar a transição ANTES do reboot e diferenciar
respostas a controle USB padrão versus vendor em estado retido, com um probe
de leitura limitado aos pedidos conhecidos (sem dados privados/registradores
arbitrários) e prova pública antes da recuperação física. Avaliar lifecycle
DWC2 antes do pedido ao PID1 somente com hipótese/diferença temporal explícita
e registro durável; o C15 foi DEPOIS da falha, não no shutdown. Não repetir
boot sem uma diferença causal ou de observação concreta. Não forçar chip-ID,
RFE, efuse ou firmware só para contornar status54.

Power cycle real da alimentação USB exige antes demonstrar o circuito e seus
consumidores; boost/otg_switch por nome ou estado não bastam. Não escrever em
GPIO/regulador nem supor que esta placa/painel represente todas as R35S/R36S.
Persistência de preferências permanece depois desse bloqueio prioritário.
