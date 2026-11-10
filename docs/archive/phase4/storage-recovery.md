# Recuperação da bancada após a Fase 3

Sessão de 23/10/2026, com conferência final retomada em 24/10/2026, America/Sao_Paulo. Continuação do [registro de interrupção](phase3-storage-stop.md), com autorização posterior do usuário para recuperar os cartões, inclusive descartando seu conteúdo se necessário. O usuário informou que o cartão do OS era uma instalação padrão recente e que as ROMs tinham backup. Essa autorização dispensa preservar uma imagem integral para esta recuperação; não autoriza concluir que o hardware está livre de defeitos.

**Estado: recuperação operacional concluída para retomar ensaios controlados.** Raiz `rw`, correção do fstab persistente, gravação/releitura após reboot aprovadas, scrub sem erros detectados e serviços originais ativos. A causa dos timeouts anteriores continua indeterminada; musplash/mmap permanece fora dos próximos testes. Não foi necessário regravar ou reparticionar os cartões.

**Seguimento:** os ensaios posteriores de menu/áudio foram executados e estão no [relatório da retomada da Fase 3](phase3-audio-resume.md). As condições abaixo descrevem o encerramento da recuperação, antes dessas novas execuções.

## Identificação e evidências anteriores ao reboot

Inventário por SSH, sem ensaio gráfico adicional:

| Mídia | Identificação nesta sessão | Partições e uso |
| --- | --- | --- |
| OS | `/dev/mmcblk0`, SS32G, 31.914.983.424 bytes | p1 FAT/BOOT; p2 Btrfs/ROOTFS; p3 exFAT/EASYROMS |
| ROMs | `/dev/mmcblk1`, SD128, 127.934.660.608 bytes | p1 FAT em `/roms2`, também exposto por bind em `/opt/system/Tools` |

Esses nomes de dispositivos valem para este boot, não são instruções para gravar uma imagem em qualquer leitor. O modelo do DT permaneceu `R36S-V12 2023-08-18 Panel 0`.

A raiz estava `ro` e `btrfs device stats /` mostrava `write_io_errs 16`, com os demais contadores em zero. O kernel continha os timeouts MMC/aborto Btrfs e BUGs de memória já registrados. O serviço `systemd-remount-fs.service` tinha falhado desde o início daquele boot, antes dos ensaios. O cartão de ROMs anunciava desmontagem incorreta no FAT.

Foram guardados localmente `build/recovery/initial-inventory.txt`, `before-reboot-details.txt`, o `fstab.original` e `boot-panel0-reference.tar.gz`. O tar contém somente `boot.ini` e os dois DTBs selecionados, não uma imagem recuperável do sistema. Nenhuma gravação foi feita no bootloader, kernel, DTBs ou tabela de partições.

## Reboot e correção do fstab

Foi solicitado reboot normal por `systemctl reboot`; o usuário confirmou retorno ao launcher. A conexão de rede voltou após reconectar o dongle. A nova raiz montou `rw`, com `kernel/tainted = 0`, sem repetição dos erros de memória/MMC/Btrfs da sessão anterior.

Os cinco contadores Btrfs reapareceram em zero **sem comando de reset**. O aborto anterior pode ter impedido a persistência dos incrementos; isso é hipótese, e a ausência dos 16 erros no contador novo não apaga a evidência do boot anterior.

O `systemd-remount-fs.service` continuava falhando com `mount point not mounted or bad option`. Foi alterado somente este token de `/etc/fstab`, preservando proprietário/permissões e usando substituição atômica com `fsync`:

```diff
-/dev/mmcblk0p2 / btrfs defaults,noatime,compress=zlib:1,ssd_spread 0 0
+/dev/mmcblk0p2 / btrfs defaults,noatime,compress=zlib,ssd_spread 0 0
```

O suporte a níveis zlib foi introduzido no Linux 4.14, posterior ao BSP 4.4.189 instalado ([documentação Btrfs](https://btrfs.readthedocs.io/en/latest/Compression.html)). A confirmação específica neste aparelho foi operacional: após `daemon-reload` e reinício do serviço, ele terminou com `status=0/SUCCESS`, e a raiz passou a anunciar:

```text
rw,noatime,compress=zlib,ssd_spread,noacl,space_cache,subvolid=5,subvol=/
```

Isso resolve a opção de montagem rejeitada. Não prova que ela causou os timeouts MMC; essa relação não foi estabelecida.

Hashes SHA-256 do fstab: original `606ccb7f423775fb8a18970240f33fa872d61bb5404ec07b1b50bed523e175e4`; corrigido `f98e9667db40beb8d084bb758913e3499d7309e5f3b954b311ebe29cc245e55c`.

## Verificações de armazenamento

Foi criado um arquivo de 16 MiB de dados aleatórios em `/var/tmp/muos-r35s-recovery/`, confirmando que esse caminho pertence à raiz Btrfs. Escrita, `fsync` do arquivo/diretório e releitura SHA-256 passaram; digest `70c5547e6d6f13cbc89a623c2718aff6e894191bc161714879ba05c63902ec80`. A persistência após outro reboot também passou, conforme a conferência abaixo.

Foi executado `btrfs scrub start -B -r -R /`, sem reparo automático. Terminou com status 0 em 6min22s, após verificar 7.753.379.840 bytes de dados e 628.424.704 bytes de árvores. Todos os contadores de erro reportados ficaram em zero:

```text
read_errors: 0
csum_errors: 0
verify_errors: 0
super_errors: 0
uncorrectable_errors: 0
unverified_errors: 0
corrected_errors: 0
no_csum: 844
```

O campo `no_csum` limita a cobertura: dados sem checksum não recebem a mesma validação. Scrub valida checksums e parte dos metadados; não substitui `btrfs check` nem testa toda a capacidade física. Mesmo com `-r`, uma raiz montada `rw` pode receber escritas administrativas ([documentação oficial](https://btrfs.readthedocs.io/en/latest/btrfs-scrub.html)). O utilitário avisou que não conseguiu configurar/restaurar limite de throughput por ausência da interface sysfs; a varredura em si terminou normalmente. Evidência completa em `build/recovery/root-scrub.txt`.

O launcher e os serviços auxiliares foram temporariamente parados para desmontar `/opt/system/Tools`, `/roms2`, `/roms` e `/boot` antes de verificar FAT/exFAT com `-n`. Nenhum desses checks foi executado sobre uma partição montada.

| Partição | Verificação | Resultado |
| --- | --- | --- |
| `/dev/mmcblk0p1` — boot | `fsck.fat -n` | status 0; 246 arquivos |
| `/dev/mmcblk0p3` — ROMs do cartão OS | `fsck.exfat -n` | status 0; clean; 1.211 diretórios e 7.005 arquivos |
| `/dev/mmcblk1p1` — cartão ROMs | `fsck.fat -n` inicial | status 1; dirty bit, rótulo inválido, cluster órfão de 32 KiB e resumo de espaço livre divergente |
| `/dev/mmcblk1p1` — reparo | `fsck.fat -a`, desmontado | status 1 com `Filesystem was changed`; removeu rótulo inválido/dirty bit e recuperou a cadeia órfã |
| `/dev/mmcblk1p1` — conferência posterior | `fsck.fat -n`, ainda desmontado | status 0; sem os erros recuperáveis anteriores |

Foi usada a ferramenta já instalada, dosfstools 4.2. A opção `-n` não grava; `-a` escolhe reparo automático e pode salvar cadeias órfãs em arquivos recuperados ([manual do projeto](https://raw.githubusercontent.com/dosfstools/dosfstools/master/manpages/fsck.fat.8.in)). Nenhuma ROM foi executada ou validada por hash nesta recuperação.

A última conferência ainda informa diferença entre setor de boot FAT e sua cópia no byte 65 (`00/01`), classificada pelo próprio fsck como geralmente inofensiva; ele não a corrigiu automaticamente e terminou em 0. Não foi feita edição manual de setor para suprimir esse aviso. Isso é distinto do dirty bit ativo da cópia principal, que foi removido.

Todos os mounts e os três serviços (`emulationstation`, `ogage`, `fn-menu-watcher`) foram restaurados e conferidos ativos. O volume corrente após o primeiro reboot era `95,95`; esse nível foi preservado ao parar/retomar serviços, sem armazenar novo mixer global. Evidências em `data-filesystem-checks.txt` e `roms-fat-repair.txt`.

## Segundo reboot e conferência após a interrupção

Depois do scrub e dos reparos, foi solicitado outro reboot normal. O usuário confirmou retorno ao launcher. A verificação remota terminou antes da interrupção da conversa, e seu log foi recuperado ao retomar:

- Boot distinto, modelo Panel 0 correto e `kernel/tainted = 0`.
- Raiz Btrfs `rw,noatime,compress=zlib,ssd_spread,...`; `systemd-remount-fs.service` terminou com `status=0/SUCCESS` neste boot, sem precisar reiniciá-lo manualmente.
- SHA-256 do arquivo aleatório de 16 MiB e do fstab corrigido preservados após o reboot.
- Hashes de `boot.ini`, DTB Linux e DTB U-Boot idênticos ao inventário anterior à recuperação.
- Cinco contadores Btrfs em zero; sem novos erros MMC/I/O, aborto Btrfs, Bad page map, Bad rss-counter ou aviso de FAT desmontado incorretamente.
- Serviços do ensaio ativos, mounts restaurados, brilho 80 e Playback `95,95`.
- Arquivo de teste e diretório removidos, com `fsync` do diretório pai; contadores continuaram em zero.

Evidência: `build/recovery/final-reboot-verification.txt`. O volume de boot FAT permaneceu funcional; não houve alteração de kernel, DTBs, bootloader ou particionamento.

Na retomada de 24/10, o console estava em outro boot. Uma nova consulta por SSH confirmou novamente raiz `rw`, mesmo hash do fstab, kernel sem taint, contadores em zero e os serviços necessários ativos. O arquivo temporário já não existia. A função `bench_health()` do supervisor da Fase 3 foi extraída por AST e executada isoladamente, passando sem parar serviços, criar uinput ou iniciar frontend. Não se executou o supervisor completo nem o novo fluxo de restauração de mixer. Evidência: `build/recovery/resumed-final-health.txt`.

Os testes demonstram recuperação operacional nesta amostra; não são certificação de toda a capacidade dos cartões, teste prolongado de alimentação/controlador ou verificação estrutural completa do Btrfs. Não foram usados `btrfs check --repair`, `zero-log`, reset de contadores ou escrita bruta em mídia montada. Os repositórios de referência e o código do port não foram alterados nesta recuperação.

## Limites para os próximos ensaios

O reboot limpa o estado tainted, mas não corrige a causa dos `Bad page map` do driver/BSP. Não repetir musplash/mmap neste kernel antes de resolver esse caminho. A relação entre esses BUGs e os timeouts do cartão continua desconhecida.

Ao encerrar a recuperação, a Fase 3 estava parcial: menu aprovado visualmente, áudio pendente e candidato com ganho128 ainda não executado. A recuperação isoladamente não aprovou esse binário, os novos fluxos de restauração de mixer ou um firmware autônomo. A validação posterior está no seguimento vinculado acima. A ressalva isolada de L3 continua como margem de erro por decisão do usuário.

O próximo ensaio mínimo é repetir somente o menu/áudio temporário com saída limitada por tempo, salvando o mixer imediatamente antes da parada dos serviços e restaurando-o depois. Conferir saúde do kernel/raiz e contadores antes/depois; interromper se surgir novo erro. Comparar a escuta com áudio conhecido do dArkOSen no mesmo nível de mixer. Não incluir musplash, submenus, Power ou mudança de firmware nessa sessão.
