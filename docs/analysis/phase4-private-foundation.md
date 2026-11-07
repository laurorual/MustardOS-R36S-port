# Fase 4 — provider privado e contrato de armazenamento

Incremento de 25/10/2026, exclusivo do R35S com modelo
`R36S-V12 2023-08-18 Panel 0`. A Fase 4 permanece aberta: esta candidata não
é uma imagem de firmware pronta para gravar.

## Decisão e limites

O usuário autorizou prosseguir com r13p0 e futuros componentes com termos
pendentes **somente para uso privado**. As consultas individuais foram adiadas.
O [registro de pendências](../../port/packaging/pending-licenses.json) reúne
origens, hashes, questões e referências; ao **fim do projeto**, gerar
`docs/licenses-to-resolve.md` a partir dele. Não considerar essa decisão uma
licença do fornecedor nem publicar os blobs/imagens antes de resolver os termos.

O ZIP Hardkernel continua sem EULA. O [rascunho de consulta](hardkernel-r13-license-request.md)
fica guardado para esse fechamento futuro. Não houve contato com terceiros.

## Provider coerente entre SDK e imagem

**Fato:** o [override Buildroot](../../port/packaging/phase4-private-provider.mk)
substitui versão, fonte local, metadados de licença e permissão de
redistribuição (`ROCKCHIP_MALI_REDISTRIBUTE = NO`) antes de avaliar a receita
nativa. SDK e target passam pela mesma receita, usando o r13p0 AArch64 do ZIP
original, sem overlay de substituição posterior ao build.

Originais fixados:

| Entrada | SHA256 |
|---|---|
| ZIP Hardkernel | `ef1a18fabf270d0a6029917d6b0e6237d328613c2f8be4d420ea23e022288dd9` |
| Membro AArch64 r13p0 | `2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea` |

O [preparador](../../port/scripts/prepare-phase4-foundation.py) verifica ambos
os hashes. Reutiliza somente headers API e templates pkg-config do provider
anterior fixado em `721653b5b3b525a4f80d15aa7e2f9df7b7e60427`, retendo seus
avisos permissivos por arquivo. Não transfere a EULA do binário anterior
para o r13p0. Os headers GBM continuam sendo o subconjunto 10.4 com o
contrato de 18 funções já exercitado; isso não afirma suporte a extensões
posteriores.

A receita define SONAME `libmali.so.1`; a finalização Buildroot também pode
remover símbolos/seções no target. A [auditoria](../../port/scripts/audit-phase4-foundation.sh)
reproduz essas transformações separadamente a partir do original, compara com
o SDK e a imagem ext4 extraída e verifica os consumidores. São transformações
pendentes de conferência nos termos finais, já registradas na lista de licenças.

O linker emite avisos `.dynsym local symbol ... >= sh_info` ao consumir esse
provider. Não foram suprimidos. O contrato GBM e o carregamento sob QEMU
passaram; isso não elimina o risco do blob nem substitui o ensaio gráfico
nativo da imagem final.

## Frontend ampliado

O [Makefile do port](../../port/packaging/phase4-frontend.mk) recompila os
módulos da UI nativa e gera `muxfrontend`, `muhotkey`, `mubattery` e quatro
bibliotecas compartilhadas para o SDK Buildroot/Cortex-A35. Usa o frontend
`5e8635b3b485eec9ad2ace141c415fd2df47d8f1` e o patch de board próprio;
Mojibake 0.3.6 é recompilado com PIC, sem biblioteca Debian.

LVGL compõe `libui`; UI dos módulos permanece com `libmuxmod`, conforme
a organização upstream. O [probe de carregamento](../../port/probes/phase4-frontend-contract.c)
resolve o grupo de dependências com `RTLD_NOW` e localiza entradas de
launcher/informações/configuração/exploração **sem chamá-las**. A primeira
tentativa de abrir bibliotecas intermediárias isoladamente foi substituída
por essa verificação do grupo usado pelo executável.

**Limite:** esse build não inclui todos os launchers de libretro/mídia/terminal,
nem aprova submenus, scripts externos ou energia. Não possui os wrappers do
menu de diagnóstico. Seu autostart fica desabilitado até um ensaio limitado
próprio; não executar seus menus de instalação/reboot no Debian anfitrião.

## Init e armazenamento de uma única mídia

O PID1, `inittab`, `rcS` e `rcK` continuam pertencendo ao Buildroot. Eudev e
D-Bus têm um único proprietário. O incremento acrescenta
[S90muos-storage](../../port/device/rk-r35s-p0/S90muos-storage), antes do core,
e [uma guarda S95](../../port/device/rk-r35s-p0/S95muos-foundation-core) que
recusa `start/status` se o armazenamento não estiver íntegro. Isso é necessário
porque o `rcS` padrão continua depois de um serviço retornar erro.

Na candidata, `/userdata` é um diretório persistente da própria raiz ext4;
um bind o apresenta em `/mnt/mmc`. Os diretórios `MUOS/...` são ligados a
`/run/muos/storage`. O adaptador preserva o contrato `key|ROM|source` de
`bindmap` e o marcador `mount_ready` de
`internal/script/device/bind.sh`, revisão
`550cc58f9cd3449a17f53ca55efcdc6c473b5a89` (GPLv3). São 22 binds de conteúdo,
21 chaves, pois `package/catalogue` e `package/config` compartilham `package`,
mais o bind de `/userdata`. Os diretórios cobrem os grupos PRIORITY/STANDARD
nativos; não incluem os binds específicos de emuladores do fim daquele script.

Trechos que definem o comportamento:

```sh
mount --bind "$src" "$dest"
printf '%s\n' "$dest" >> "$state/mounts"
mount -o remount,bind,nosuid,nodev "$dest"
```

O journal permite desfazer apenas os mounts criados pelo serviço, em ordem
inversa. Um mount preexistente é recusado e preservado; não há `umount -l`.
A comparação exige leitura bem-sucedida de device/inode, além de igualdade.
`mount_ready` só aparece após concluir todas as operações. `start/stop`
podem ser repetidos, e a guarda recusa binds que apontem ao diretório errado.

**Escolha deliberada para bring-up:** não há descoberta de blocos, formatação,
particionamento, swap, expansão automática, SD2 ou execução de `init/oops.sh`.
O boot FAT/labels/UUIDs e a segunda mídia continuam para o conjunto de boot.
Isso reduz o primeiro contrato a armazenamento já montado pelo kernel.

## Verificação e riscos restantes

O primeiro ensaio nativo encontrou ausência de `stat` e uma comparação que
aceitava duas saídas vazias. Esse resultado foi **invalidado**, apesar do
status0 do executor. A correção habilita `CONFIG_STAT` e
`CONFIG_FEATURE_STAT_FORMAT` em um
[fragmento BusyBox](../../port/device/rk-r35s-p0/phase4-foundation.busybox),
confere os comandos antes de montar e rejeita falhas nas leituras de identidade.
O ensaio posterior inclui detecção de um bind deliberadamente errado.

**Resultado aprovado da repetição:** storage/core inicializaram e pararam
nativamente com a nova libc; rollback, preservação de mount preexistente,
identidade incorreta e escrita através dos binds passaram. Não houve parada
dos serviços do launcher. O fixture tmpfs foi desmontado e a sessão removida;
coleta final: taint0, cinco contadores Btrfs zerados, serviços ativos e o mesmo
hash do kernel instalado. Não foram expostos nós de blocos, GPU, input ou áudio.

| Artefato privado auditado | SHA256 |
|---|---|
| Rootfs ext4, 512 MiB / 281 ELF | `43a692d1ef877d60b423a757bbad8305d247022bb67ed632bfa8d890be32ae16` |
| Mali no SDK, com SONAME | `b3553876c57c1daacb5c76971e22e81db1f9d8833021c68d1bd2cbd40f280dd8` |
| Mali na imagem, após strip | `00628ed93c32c6d529f656ca8be44c92846c7076040ddd5e9a15d008385aca9d` |
| Tar da imagem extraída para RAM | `8cd70d2397f6b9a36f0c4838a5492117b7e811ef5ab5ccc59efb9d2e6a6a3ad6` |

Os hashes SDK/target são diferentes por causa do strip verificado; não são
dois providers de origens distintas. O tar é um staging privado de teste,
sem tabela de partições ou cadeia de boot.

As provas desta candidata ficam em `build/phase4/foundation/`: logs de provider,
frontend e imagem, `provider-manifest.json`, `overlay-manifest.json`,
`audit/`, `staging.*/staging-manifest.json` e `native-storage.*/evidence/`.
Os tarballs/imagem que contêm Mali permanecem privados. Resultados finais e
hashes devem ser consultados no manifesto do checkpoint, sem transferir a
aprovação do menu anterior para o frontend ampliado.

O [checkpoint de prova](../../dist/phase4/private-foundation/build-manifest.json)
em `dist/phase4/private-foundation/` arquiva fontes, binários próprios, auditoria,
sessão aprovada e tentativa inicial invalidada, com `SHA256SUMS`. Exclui ZIP/Mali,
imagem e tar de runtime. Não é firmware gravável nem pacote de execução
independente. Os campos `firmware_boot_tested` e `frontend_full_native_tested`
continuam `false`.

Faltam: coldplug e ordem completa no boot real, bindings de emuladores/manifestos,
persistência da configuração final, volume/brilho reais, gerenciamento de
energia, áudio original da ajuda e execução limitada do frontend completo.
Os 555 módulos já compilados do BSP ainda não foram incluídos neste rootfs;
essa integração, seus índices e os firmwares efetivamente necessários devem
ser verificados antes do conjunto de boot.
O kernel candidato e a cadeia própria U-Boot/DDR/BL31/BL32 continuam sem boot.
O ensaio de storage em tmpfs valida binds e ciclo de vida, sem comprovar
persistência após reboot nem características do ext4.

**Continuação:** o [frontend ampliado](phase4-full-frontend.md) foi executado
depois deste checkpoint, com recursos adicionais e correção do caminho de
volume no staging. Submenus, áudio e helpers reais passaram. Isso não modifica
retroativamente a imagem/SHA acima; o próximo incremento deverá incorporar
esses deltas à receita antes de validar o conjunto de boot.
