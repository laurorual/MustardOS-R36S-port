# Por que a base atual não é uma imagem G350 modificada

O port reutiliza muOS e componentes Linux existentes. A expressão “SO do
zero” descreve mal o que foi feito: a maior parte do código original do
port é perfil de hardware, integração de build e diagnóstico temporário.
Não implementamos kernel, libc, init, servidor de áudio ou frontend novos.

| Parte | Base efetivamente reutilizada | Adaptação necessária neste aparelho |
|---|---|---|
| Interface, recursos e serviços muOS | MustardOS frontend/internal/tool, revisões fixadas | Perfil rk-r35s-p0, patches pequenos e integração dos serviços |
| Input | muinput e frontend originais | Mapeamento observado no GO-Super/odroidgo3-keys; não copiar trocas/inversões G350 |
| Kernel/DTB | BSP RK3326 existente, recompilado, e DTS da família R35S | Delta Panel0, opções/drivers e módulos correspondentes ao próprio build |
| U-Boot | Fonte Rockchip existente e payloads DDR/trust identificados | Perfil Panel0, mapa de memória e remoção de caminhos automáticos de recovery inadequados ao ensaio |
| Rootfs | Buildroot, glibc, BusyBox, SDL, PipeWire/WirePlumber e demais pacotes existentes | Sysroot coerente com kernel4.4, bibliotecas/provedor Mali e layout muOS |
| Testes C01–C07 | Componentes nativos acima | Harness para isolar boot, storage, RNG, input, gráficos, áudio e agora rede |

Evidência de reutilização direta:
`port/buildroot/package/muos-core/muos-core.mk:27–30` instala os scripts e
recursos de internal e sua licença; `port/scripts/prepare-phase4-core.py`
fixa as revisões e aplica o perfil/patches. O rootfs usa as receitas do
Buildroot fixado, não uma implementação própria desses pacotes.

## O que o G350 já oferece

O G350 é uma referência relevante porque compartilha RK3326/AArch64 e os
contratos de userspace muOS. Seus diretórios e o Pixel2 foram examinados
desde a matriz inicial. Isso permite reaproveitar organização e conceitos;
não significa que um boot de uma imagem G350 adaptada tenha sido testado.

`refs/muos/internal/device/rk-g350-v/package/boot.ini:3–15` define raiz
ext4, seleciona `rk3326-batlexp-linux{,1}.dtb` por hwrev e chama booti.
O pacote inclui Image e uboot.img. Esses arquivos são payloads, não a receita
completa de reconstrução do rootfs/boot para R35S nos três refs examinados.
Ausência dessa receita identificada não prova que ela inexista no upstream.

Diferenças concretas no perfil local:

- `device/rk-g350-v/config/audio/control` contém `digital volume`; o codec
  exercitado neste R35S usa `Playback`, e o ensaio revelou a necessidade
  de SPK_HP. Copiar o perfil não resolveria essa descoberta por si só.
- `config/network/module` aponta para r8188eu; o dongle presente é8821cu,
  com modo inicial1a2b que exige ejeção antes de c820.
- DTBs do BatleXP não estabelecem timings/sequência do R36S-V12 Panel0.
  O perfil de input e os caminhos de bateria/backlight também precisam de
  confronto com o hardware, como registrado na matriz.

## A alternativa continua tecnicamente válida

Usar uma imagem oficial G350 como base e trocar somente BSP/perfil é uma
estratégia possível de protótipo. Não foi demonstrado que seus binários
sejam incompatíveis, nem medido quanto tempo essa alternativa pouparia.
Ela exigiria inventariar rootfs/loader/bibliotecas, manter kernel+módulos+
DTB+Mali coerentes e validar as mesmas funções no R35S. Mesmo SoC e ISA
não dispensam isso. Não há base para prometer “basta trocar o DTB”.

A escolha atual privilegiou uma base recompilável com ABI conhecida e um
BSP aderente ao Panel0, em vez de depender de alterações sobre uma imagem
binária ainda não auditada. Há custo: compilar pacotes e validar cada
contrato é mais demorado que começar de um rootfs pronto. Os muitos boots
de áudio e sua instrumentação aumentaram esse custo; não eram novas funções
de um SO, mas investigação de falhas de rota/ganho/recursos.

Agora a candidata já inicia U-Boot/Linux/rootfs próprios e executa os
componentes muOS reutilizados. Substituir toda a base neste ponto perderia
essa evidência sem ganho medido. A direção é consolidar os deltas pequenos
e aposentar o harness quando houver critérios equivalentes no init final.
O C07 foi antecipado justamente para reduzir trocas físicas e acelerar
iteração remota. A comparação com uma imagem G350 pode ser feita offline
se uma lacuna específica justificar, sem migrar automaticamente a base.
