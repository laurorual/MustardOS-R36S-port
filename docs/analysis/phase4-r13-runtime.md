# Fase 4 — diagnóstico local Hardkernel r13p0 no rootfs próprio

Retomada de 24/10/2026, após a [rejeição da candidata UK 10.6](phase4-graphics.md).
**Resultado:** contexto EGL/GLES, render/readback de buffer e ensaio SDL/KMSDRM
na tela passaram no BSP instalado. O usuário confirmou cores, orientação,
movimento e retorno normal ao launcher. **A licença de redistribuição do blob
continua pendente; não há novo firmware ou imagem Buildroot aprovada.**

## Proveniência recuperada

A [receita Batocera fixada em 5f6d4f30…](https://github.com/batocera-linux/batocera.linux/blob/5f6d4f30fa6245c7f4a38bd18f3fd876e42be720/package/batocera/gpu/mali-g31-gbm/mali-g31-gbm.mk)
aponta para um pacote Hardkernel específico RK3326/r13p0. Seu
[arquivo de hashes](https://github.com/batocera-linux/batocera.linux/blob/5f6d4f30fa6245c7f4a38bd18f3fd876e42be720/package/batocera/gpu/mali-g31-gbm/mali-g31-gbm.hash)
fixa o checksum do ZIP. Isso forneceu uma origem mais concreta que o nome
genérico rxp0 em `rk3326_core_builds`; a receita foi lida, não executada nem copiada
para o port.

O acesso automatizado a `dn.odroid.com` e à nota no wiki recebeu 403/desafio
Cloudflare. O usuário baixou o ZIP pelo navegador para `build/phase4/mali-r13/`.
O preparador verificou o hash **antes** de ler seus membros:

| Item | Identidade verificada |
| --- | --- |
| ZIP | `rk3326_r13p0_gbm_with_vulkan_and_cl.zip` |
| URL do distribuidor | `https://dn.odroid.com/RK3326/ODROID-GO-Advance/rk3326_r13p0_gbm_with_vulkan_and_cl.zip` |
| SHA256 ZIP | `ef1a18fabf270d0a6029917d6b0e6237d328613c2f8be4d420ea23e022288dd9` |
| Membro AArch64 | `libmali.so_rk3326_gbm_arm64_r13p0_with_vulkan_and_cl`, 40.867.064 bytes |
| SHA256 membro | `2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea` |
| Git blob SHA1 calculado | `2083f5386c201abc8f2e697e8004a14e59524a86`, igual ao binário instalado e ao ref anteriormente identificado |

**Fato:** o ZIP contém apenas os dois binários arm64/arm32; não traz EULA,
headers ou fontes. O EULA do pacote JeffyCN anterior não foi estendido a esse
arquivo por analogia. A identificação fecha a origem do binário de teste,
sem fechar o direito de redistribuí-lo. O nome do ZIP também não comprova
Vulkan/OpenCL: nenhum dos dois foi testado.

## Overlay de diagnóstico e ABI

O [preparador](../../port/scripts/prepare-phase4-r13-diagnostic.sh) extrai a
imagem gráfica finalizada com debugfs/fakeroot para uma árvore nova. Substitui
somente a biblioteca Mali nessa árvore temporária, preserva o membro original
e ajusta o SONAME da cópia de runtime para `libmali.so.1`, registrando ambos
os hashes. Não altera o SDK, a imagem ext4 original, as bibliotecas instaladas
no Debian ou os artefatos das provas anteriores.

Base: SHA256 ext4 `40b24bb1…3a167`, SDK Buildroot/GCC 13.4/glibc 2.41,
libdrm 2.4.124 e SDL 2.30.12 com os três ajustes GBM documentados anteriormente.
O ZIP não oferece headers; este ensaio usa o subconjunto GBM verificado do
SDK existente e resolução dinâmica SDL das funções opcionais. Não é uma
receita final de desenvolvimento/empacotamento do provider.

O ELF r13p0 requer libc/libm/libdl/libpthread/librt, libdrm, libstdc++ e
libgcc_s. Os contratos de símbolos/carregamento passaram em QEMU Cortex-A35
com `LD_BIND_NOW=1` usando as bibliotecas da árvore nova, inclusive C++.
Compatibilidade não foi inferida do resultado no Debian: foi ensaiada de
novo no conjunto de userspace do port.

O [runner](../../port/scripts/run-phase4-r13-session.sh) confere o staging,
usa namespaces privados e `/tmp` tmpfs, sem expor framebuffer/input/ALSA ou
ligar bibliotecas Debian ao chroot. Áudio e muinput ficam desligados. O
supervisor/gravador Python e o kernel/coldplug permanecem os do dArkOSen;
isso não valida o kernel candidato, eudev, PID1 ou boot da imagem própria.

## Testes executados, em ordem

1. **Contexto/buffer sem modeset.** O [probe EGL](../../port/probes/phase4-egl-context.c)
   abre DRM, cria uma superfície GBM 64×64 e contexto GLES2, limpa e lê um pixel.
   Não chama drmModeSetCrtc, atomic commit ou outro modo de apresentação KMS.
   Obteve EGL 1.4/ARM, Mali-G31, OpenGL ES 3.2 r13p0 e
   `readback_rgba=32,128,191,255 gl_error=0x0`; exit 0.
2. **Tela SDL por 30 segundos.** Só após a prova anterior, executou o probe
   de quadrantes recompilado para o SDK novo. KMSDRM, opengles2 acelerado/vsync,
   640×480, renderer Mali-G31 e readback vermelho passaram. Registrou 1797
   frames em 30,008 s: **59,884 fps**, mediana 16,682 ms, p95 16,939 ms,
   `render_failures=0`, exit 0. O usuário confirmou tudo correto.
3. **Parada e restauração.** Nos dois ensaios, mixer inicial/final idêntico,
   serviços previamente ativos restaurados, taint 0, cinco contadores Btrfs
   zero, root/boot rw e Image instalado sem alteração. Não surgiram os
   marcadores de erro antigos no dmesg. Os diretórios remotos foram removidos
   somente depois da coleta e verificação das evidências.

O supervisor limita o worker a 110 s e arma restauração independente a 150 s.
Restauração normal foi testada; perda de SSH não foi injetada. A confirmação
visual e os números são de um teste curto deste Panel 0; não aprovam outros
painéis, cursor de hardware, RGA, consumo/suspensão ou estabilidade prolongada.

## Evidências e próximo incremento

Em `build/phase4/mali-r13/`: ZIP original, membro preservado, receita/hash
consultados, ELF, logs QEMU, manifests da base/overlay, scripts exatos e
evidências dos ensaios indicadas por `latest-egl-context`/`latest-graphics-r13`.
O arquivo `diagnostic-staging.tar.gz` permanece somente na área local de build.
Não foi gerada imagem ext4 com esse blob. O pacote de evidências
`dist/phase4/r13-runtime-diagnostic/` exclui o ZIP, a biblioteca e o staging
que a contém; não é um pacote de firmware ou de redistribuição do driver.
A candidata gráfica original permanece arquivada com seu resultado rejeitado.

**Continuação de 25/10:** o [primeiro menu no userspace próprio](phase4-menu-own-rootfs.md) recompilou dependências/frontend e passou em tela/input/áudio SDL/PipeWire. O r13p0 permanece como substituição privada no staging; a ausência de termos vinculados ao ZIP continua sem resolução.

Próximos passos concretos:

- Obter do distribuidor Hardkernel/ARM os termos aplicáveis ao ZIP/hash exato,
  incluindo condições de redistribuição e eventuais modificações/SONAME. Não
  houve contato enviado a terceiros.
- Com os termos fechados, definir provider Buildroot coerente para SDK/target,
  fixar fontes/headers/hashes/avisos e reconstruir/auditar a imagem inteira.
  O sucesso de um overlay de runtime não substitui essa integração.
- Conferir o mapping da SDL nova, recompilar as dependências do frontend e
  repetir o primeiro menu no rootfs próprio; manter a prova de
  [uinput real](phase4-native-input.md) separada da prova SDL/controller.
- Integrar init/storage completos e fechar cadeia de boot; só depois preparar
  um teste independente de kernel/rootfs em cartão separado na Fase 5.
