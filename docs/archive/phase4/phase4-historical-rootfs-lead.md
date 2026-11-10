# Fase 4 — referência histórica adicional de rootfs

Durante a investigação da biblioteca Mali em 24/10/2026, a busca encontrou
[`cmclark00/mustardroot_external`](https://github.com/cmclark00/mustardroot_external/tree/12d69c56405b4b06ec976fc1850ccf636de714e8).
É uma referência pública adicional; não foi demonstrado que seja o processo
oficial atual de construção do muOS. O README contém apenas a descrição
breve do projeto. Nenhum script foi executado nem código incorporado ao port.

Na revisão fixada há `Config.in`, `external.mk`, `external.desc` e os arquivos
`configs/muos_a133_defconfig` e `configs/muos_v11wip_defconfig`. Este último
seleciona AArch64, Cortex-A53 e toolchain Buildroot/glibc/C++; isso não o
torna adequado automaticamente ao Cortex-A35/RK3326 ou ao kernel 4.4 do alvo.
Também seleciona BusyBox init, eudev, D-Bus, Bash, PipeWire/WirePlumber e
SDL2 com image/mixer/ttf; os hooks/overlay de rootfs estão vazios nesse
defconfig. A combinação de `pipewire-media-session` e WirePlumber não deve
ser transportada sem decidir quem realmente administra a sessão.
O pacote `package/mustardOS/gpu/mali-g31-gbm/mali-g31-gbm.mk` usa o mesmo
download Hardkernel r13p0 encontrado na receita Batocera, sem resolver a
ausência de licença no ZIP adicional.

Serve como pista para comparar seleção de pacotes, overlay/init e contratos
de userspace na próxima investigação. Antes de copiar implementações, fechar
licenças e proveniência por arquivo e conferir o vínculo com os três refs
muOS usados neste port. Não substitui o SDK próprio já testado nem permite
tratar esses defconfigs como receita reproduzível do firmware atual.
