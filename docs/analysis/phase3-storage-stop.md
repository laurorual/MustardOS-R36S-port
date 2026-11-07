# Suspensão dos ensaios: erros de kernel e armazenamento

Ocorrências constatadas em 23/10/2026, America/Sao_Paulo, ao encerrar testes de menu/áudio. Este registro **impede declarar a Fase 3 integralmente aprovada ou a bancada íntegra**. O kernel foi examinado depois dos ensaios; a detecção tardia não transforma as execuções anteriores em provas de estabilidade.

**Continuação autorizada posteriormente:** o usuário dispensou preservar o conteúdo dos cartões e autorizou recuperação/regravação se necessária. As ações posteriores, incluindo reboot normal e correção do fstab, estão no [relatório de recuperação](storage-recovery.md). As descrições abaixo registram o estado na suspensão original; não representam o estado mais recente do aparelho.

## Fatos observados

O inventário inicial do usuário mostrava raiz Btrfs `rw`. A conferência posterior da Fase 3 encontrou `/dev/mmcblk0p2` como `ro` em `/proc/mounts` e `findmnt /`. O kernel explica a transição:

```text
[14931.938608] mmcblk0: error -110 sending status command, retrying
[14931.950785] mmcblk0: error -110 sending status command, aborting
[14931.998957] blk_update_request: I/O error, dev mmcblk0, sector 17400328
[14932.250360] BTRFS: error ... in btrfs_commit_transaction:2124: errno=-5 IO failure
[14932.262566] BTRFS info (device mmcblk0p2): forced readonly
[14932.262591] BTRFS: Transaction aborted (error -5)
```

Os números entre colchetes são segundos desde o boot. O registro contém dez erros de escrita Btrfs e tentativas do driver de resetar/retunar o cartão. Não foi o agente que executou um remount da raiz para `ro`; a atribuição inicial aos binds privados foi corrigida após ler o kernel. Os binds privados também aparecem `ro`, mas isso não basta para atribuir a eles a falha de I/O.

`statvfs('/').f_flag` **não** anunciou ST_RDONLY nessa situação, embora `/proc/mounts` e o kernel informassem a raiz forçada para leitura. Por isso a nova trava não confia somente em `statvfs`.

Também há registros **anteriores** aos erros MMC:

```text
[13090.441444] BUG: Bad page map in process musplash
[13090.558053] BUG: Bad rss-counter state
[13148.759336] BUG: Bad page map in process musplash
[13193.751638] BUG: Bad rss-counter state
```

Eles correspondem a processos musplash da sessão de testes anterior; o kernel já estava tainted antes do erro Btrfs. Isso acrescenta um risco do kernel/BSP ao caminho de framebuffer/mmap, mesmo com confirmação visual dos pixels. Não repetir o ensaio de musplash/mmap nesse kernel como se a aprovação visual comprovasse segurança do driver.

Na leitura final, a bateria anunciou 100%, 4,146V, health Good e AC online. Esses valores não excluem instabilidade de alimentação, contato ou bugs de driver; não foram medidas as tensões durante o erro.

## O que permanece hipótese

- A causa física/lógica dos timeouts não foi determinada: cartão, contato, controlador, alimentação ou kernel precisam de investigação própria.
- Não foi provada relação causal entre `Bad page map`, carga gráfica/áudio e falha MMC. Os eventos ocorreram na mesma sessão de uso, em momentos distintos.
- Não se pode prometer integridade do Btrfs nem concluir que um reboot/remount resolve a causa.
- O áudio fraco não deve ser atribuído automaticamente ao cartão. O mixer produziu dados não nulos; a escuta continuou insuficiente, e houve interferência do retorno dos serviços no nível de volume.

## Ações executadas e limites

Os ensaios no aparelho foram suspensos. Não houve remount `rw`, fsck, `btrfs check --repair`, reset de contadores, gravação de imagem, alteração de partições, atualização de kernel/DTB ou reboot pelo agente. Nenhum teste adicional de armazenamento ou escrita foi usado para provocar/reproduzir a falha.

EmulationStation, ogage e Fn watcher voltaram ativos. O retorno desses serviços repôs Playback em95/237 apesar de o usuário ter aumentado para142; o agente restaurou **apenas o controle ALSA volátil** para142/237, correspondente ao nível escolhido. Isso não garante persistência de configuração em uma raiz com erro. Brilho permaneceu80.

O [supervisor da Fase 3](../../port/scripts/phase3-device-session.py) agora recusa testes antes de parar serviços quando a raiz está `ro` ou o dmesg deste boot contém os erros MMC/Bad page/aborto Btrfs. A recusa na raiz `ro` foi verificada no aparelho sem iniciar menu ou muinput. A preservação de volume antes/depois dos serviços foi acrescentada ao código, mas sua execução positiva futura continua pendente: não se usou a bancada com falha para validar o novo fluxo.

Os diagnósticos relevantes foram copiados para `build/phase3/`: `root-readonly-investigation.txt`, `kernel-storage-errors.txt`, `post-audio-state.txt`, `user-volume-restored.txt`, `health-guard-refusal.txt`. O diretório temporário em tmpfs foi removido após conferir ausência de processos/timers do ensaio; a conexão SSH do agente foi encerrada. A limpeza não repara nem altera o estado `ro` do cartão.

## Condição estabelecida na suspensão original

Primeiro preservar os dados/cartão com cópia verificável em ambiente e mídia apropriados, antes de qualquer tentativa de reparo. Definir leitor, destino e capacidade da cópia com o usuário; não foi iniciada uma imagem ou operação de recuperação nesta fase.

Depois investigar a falha fora da instalação de referência, preferencialmente sobre uma cópia/cartão de teste. Reparo, reboot, retirada de mídia e nova gravação precisam de plano explícito; nenhum deles foi autorizado como extensão automática do ensaio de menu. Não emitir comandos de reparo genéricos como solução já validada.

A autorização posterior dispensa a cópia integral nesta recuperação porque o usuário aceita perder os dados. As verificações de saúde abaixo continuam necessárias; a dispensa de backup não comprova integridade nem resolve a causa física/lógica.

Só retomar testes nativos com armazenamento saudável, raiz com estado esperado e um boot sem os erros de memória/MMC registrados. Antes de reutilizar musplash, resolver especificamente o caminho de mmap desse BSP. Revalidar também brilho, mixer e serviços antes/depois de cada sessão. A Fase 4 permanece não iniciada.
