# Fase 4 — C02: prontidão e persistência de entropia

**Estado: recorte C02 aprovado**, com primeiro boot seedless e um boot
persistido corrigido, logs coletados e retorno saudável ao dArkOSen.
O rcS completo e a segurança criptográfica do kernel legado não foram
aprovados. Kernel/DTB/U-Boot e tabela de partições não mudaram neste incremento.

## Resultado observado

| Rodada | Estado de entrada | Resultado |
|---|---|---|
| Primeiro boot C02 | Sem seed | Pronto após 8013 ms; seed creditável criado, input/parada/fsck aprovados |
| Tentativa seguinte | Esperado persistido | Erro não transcrito; causa exata daquela mensagem não recuperada |
| Retry dessa tentativa | Sem seed creditável | Passou após 7813 ms; consumiu seed sem crédito; **não aprova caminho persistido** |
| Revisão 1, BOOT0001 | Persistido | Parou após 5010 ms sem prontidão; logs identificaram prazo insuficiente |
| Revisão 1, BOOT0002 | Sem seed creditável | Passou após 6814 ms, consumindo sem crédito |
| Prazo corrigido, BOOT0003 | Persistido | **Passou na primeira tentativa**, pronto após 7114 ms; refresh nativo e parada aprovados |

O último boot consumiu 2048 bits com crédito, salvou conservadoramente
um seed não creditável, aguardou getrandom pronto e pediu nova geração ao
applet nativo. Este consumiu o arquivo conservador **sem crédito** e gerou
um novo seed creditável. A parada voltou a consumir/gerar seed creditável.
Metadados: root:root, 0400, 256 bytes; diretório 0700. Nenhum byte ou hash
do seed foi coletado.

O único aviso prematuro no último dmesg é do próprio applet:

```text
[    5.038334] random: seedrng: uninitialized urandom read (256 bytes read, 55 bits of entropy available)
```

Ele permanece na prova; sua saída foi tratada como não creditável. Não
houve aviso prematuro de consumidores. Inicialização do pool precedeu
udevd; D-Bus RPC, controle muinput, mapping SDL e liberação passaram.
Status final 0, taint 0, raiz ext4 read-only, FAT de logs desmontada,
fsck offline sem erros. Report em uptime 17,81 s. Isso é uma sessão curta,
não uma prova de estabilidade prolongada ou de qualidade da entropia.

Após retorno: Image original `31bdb671…b0577` inalterado, taint 0, cinco
contadores Btrfs zerados, ES/ogage/Fn ativos e nenhuma unidade muos carregada.
Temporários removidos, raiz candidata desmontada. As montagens FAT globais
feitas pelo dArkOSen foram preservadas; somente o bind privado de coleta
foi desmontado.

## Evidências e diagnóstico da parada

C01 havia registrado urandom ainda não inicializado por udev aos 5,0 s e
pool pronto aos 9,073 s. O kernel fixado tem HW_RANDOM=y, porém
HW_RANDOM_ROCKCHIP e CRYPTO_DEV_ROCKCHIP_V2 desativados. DTS habilitado não
prova driver ativo ou qualidade desse hardware; esse conjunto não mudou.

Fonte primário local:

- `build/phase4/linux-base/drivers/char/random.c:1566`: RNDADDENTROPY mistura
  e credita **input_pool**.
- Mesmo arquivo, `:1619`: getrandom depende de **nonblocking_pool.initialized**.
- `:675`: inicialização por pool e transferência assíncrona; creditá-lo não
  garante prontidão imediata do outro pool.
- `:1471`: urandom registra aviso antes da extração.
- `build/phase4/graphics-config/output/build/busybox-1.37.0/miscutils/seedrng.c:101`:
  EAGAIN e GRND_INSECURE não suportado levam ao fallback conservador.
- Mesmo arquivo, `:135`: consumo remove o seed e fsynca seu diretório
  antes do crédito; `:249` distingue a gravação creditável/conservadora.
- `entropy.8nhre_uw/extracted/etc/init.d/S01seedrng`, sob
  `build/phase4/linux-diagnostic/`: script Buildroot mascara falhas do
  applet com `|| true`; só seu exit status não basta.

BOOT0001 preservou:

```text
mode: persisted
Seeding 2048 bits and crediting
Saving 2048 bits of non-creditable seed for next boot
rng_ready=0 wait_ms=5010
```

Udev/input não iniciaram; o pool só ficou pronto aos 11,456 s de uptime.
Portanto **essa parada** é atribuída ao prazo de 5 s. O comportamento
reproduz a explicação de pools do fonte; a mensagem exata da tentativa
anterior perdida continua desconhecida. Não há evidência para atribuir a
falha ao contato do cartão.

## Política e alteração mínima

[S05](../../port/device/rk-r35s-p0/S05muos-entropy) e sua
[biblioteca](../../port/device/rk-r35s-p0/entropy-diagnostic/functions.sh)
chamam S01 nativo com `-d /var/lib/muos-seedrng`. Exigem diretório root:root
0700 na ext4 de / e arquivo regular sem symlink, 0400, link count 1,
32–256 bytes. Verificam saída, metadados e prontidão real.

Sem seed creditável, aguardam getrandom(GRND_NONBLOCK) por até 60 s antes
de chamar S01 e udev. Com seed, consomem pelo applet e também aguardam até
60 s. Se a primeira gravação foi conservadora, só **após prontidão** pedem
nova geração nativa. Nunca renomeiam seed.no-credit para seed.credit,
creditam timestamps/bytes conhecidos ou provisionam seed do host.

O [probe](../../port/utils/muos-rng-ready.c) consulta um byte e imprime
somente prontidão/tempo. Não salva nem imprime esse byte. Erros/ENOSYS não
viram sucesso. S05 é limitado externamente a 90 s; demais comandos, 45 s.
I/O preso dentro do kernel não tem cancelamento rígido garantido.

O runner inicia S05 antes da cadeia C01 e o para por último. Incrementa
contador público antes dos serviços e salva DIAG04/BOOTnnnn, além da cópia
mais recente. Falhas antes do runner ou da montagem FAT ainda podem exigir
transcrição visual. [Coletor](../../port/scripts/collect-phase4-linux-logs.py)
lê somente esses logs FAT em namespace privado/ro; não lê a raiz privada.

A primeira correção alterou dois arquivos: política e runner de logs.
Após reproduzir a falha, a segunda mudou **somente** o prazo 5 → 60 s na
biblioteca. O [instalador](../../port/scripts/install-phase4-service-diagnostic.py)
revision_update=2 exige exatamente esse replace, preimages, CIDs/capacidade,
PARTUUID, root candidato desmontado e saúde do original. Preserva o seed;
backup cobre somente código. Fsck offline passou após cada atualização.
Rollback existe, mas não recebeu injeção destrutiva nesta rodada.

## Verificação e artefatos

O [preparador](../../port/scripts/prepare-phase4-entropy-diagnostic.py)
clona o C01 host sem seed e audita ext4/fsck, extração, ELF, shell e
Cortex-A35/QEMU. Sete casos do probe exercitam ready, EAGAIN, EINTR, ENOSYS,
short read e prazo inválido. Treze fixtures de política cobrem o fluxo
normal, refresh, prontidão tardia/ausente, falha mascarada e metadados ruins.
Usam dados fictícios locais; não fazem crédito no kernel. Blocos reais do
runner preservaram dois arquivos por boot e recusaram contador inválido.
O [analisador](../../port/scripts/analyze-phase4-entropy-boot.py) confere
modo, consumo/rotação, prontidão antes de udev, arquivo por boot, input,
root ro, fsck e saúde do retorno.

Blueprint final **sem seed**: `build/phase4/linux-diagnostic/entropy.rg3vmy8n`.
Transação: `deadline-update`; última coleta: `boot4`, BOOT0003.
O marcador de formato do runner continua revisão 1. Imagem host não é dump
do cartão vivo. Não reinstalar o overlay C02 inicial sobre estado privado.

Provas imutáveis separadas:

- `dist/phase4/entropy-diagnostic-preboot/` e `native-entropy-first/`.
- `dist/phase4/native-entropy-retry-seedless/`: retry não persistido.
- `dist/phase4/entropy-diagnostic-r1-preboot/` e `native-entropy-deadline/`:
  correção inicial e parada reproduzida, incluindo BOOT0001/BOOT0002.
- `dist/phase4/entropy-deadline-preboot/`: correção exata do prazo.
- `dist/phase4/native-entropy-persisted/`: consumo persistido corrigido,
  BOOT0003 aprovado, históricos preservados e saúde final.

## Limites e próximo incremento

A prontidão operacional de getrandom não comprova qualidade do hardware
RNG, segurança do random.c legado ou entropia anterior a PID 1/AT_RANDOM.
Não clonar/distribuir a raiz viva com seed, nem coletar conteúdo/hash do
estado privado. Licenças pendentes permanecem para uso privado e relatório
único ao fim do projeto.

S05 pertence ao diagnóstico C02; não basta copiá-lo e executar rcS completo:
o rcS padrão executaria S01 antes de S05. A integração de produto deve
ordenar o consumo nativo sob uma única política, sem consumo antecipado
duplicado, e validar persistência no shutdown normal.

Próximo menor teste: SDL/GLES com duração limitada no kernel próprio,
antes do menu/áudio, mantendo logs por boot, seed vivo, serviços
supervisionados e retorno ao diagnóstico parado/root ro. UI/áudio/GLES no
kernel próprio, eventos físicos, Wi-Fi, energia/shutdown e outros painéis
continuam sem aprovação nesse conjunto. A Fase 4 permanece aberta.
