# C82 — backup offline e cópia independente aprovados

Concluído em **04/11/2026**. O test128 permaneceu no Steam Deck Jupiter,
IP192.168.15.13. Backup fresco640MiB, FAT/raiz extraídas, seis arquivos privados
C80/boot72 e nove arquivos de preferências/saves foram conferidos no Deck e
neste computador. Fsck FAT/raiz/p3 retornou0; cartão desmontado e snapshot root
removido. Nenhum writer de firmware, reparo de metadata, provisionamento,
restore, carregamento de seed ou boot foi executado.

**Pendência real:** SteamOS alterou os modos das raízes p2/p3 para0777 durante
o automount inicial. O backup preserva essa situação fielmente; não qualifica
boot ou restauração indiscriminada. Corrigir os modos0755 por operação própria
limitada, com backups guardados, antes de retornar o cartão ao R35S. Recuperação
pós tentativa de boot com seed fresco/sem crédito e contador monotônico continua
necessária antes de instalar/bootar uma candidata C79.

## Falha inicial e diagnóstico sem reler o cartão

SSH precisou ser ativado localmente e a chave pública reinstalada: ela havia
sido removida na limpeza C20 anterior. Chave do servidor conferida por pin,
sem aceitar chave nova. Survey identificou CID/capacidade/setor do test128,
ferramentas presentes e espaço suficiente em `/var/tmp` ext4. Original32 fora
do fluxo. P2/p3 estavam montadas automaticamente em rw; foram desmontadas
normalmente por `udisksctl`, sem force.

Primeiro helper C81 retornou `ValueError`, sem recibo completo. Sua parcial
`/var/tmp/muos-r35s-c81-backup.chy99nhv` ficou root0700, sem cópia válida no host.
A investigação foi interrompida pelo pedido de [limpeza do SSD](storage-cleanup.md)
e retomada depois, com as partições ainda desmontadas.

Auditor finito `audit-phase4-backup-private.py` lê somente a raiz regular da
parcial. Copia fontes verificadas para snapshot root, não abre nem monta
nenhum dispositivo e não executa código da imagem. Dois diagnósticos locais
confirmaram boot72 e a recusa `Private parent alias/owner/mode`. A extensão
exportou uma cópia privada da raiz parcial para análise local. Pais observados:

| Caminho | Dono/modo |
| --- | --- |
| / | root:root0777 |
| /etc, /var, /var/lib | root:root0755 |
| /var/lib/muos-network, muos-seedrng, muos-diagnostic | root:root0700 |

O código instalado em `/usr/lib/hwsupport/steamos-automount.sh`, linha99,
aplica `chmod 777` ao ponto de montagem se ele não for gravável pelo usuário
`deck`. A condição explica a alteração após o automount rw observado. Script
consultado somente para leitura; hash registrado em evidência privada. Não foi
copiado nem modificado o subsistema do SteamOS. A raiz p3 também foi confirmada
em0777 durante o backup revisado.

## Correção limitada ao contrato de backup

O contrato padrão do núcleo continua exigindo0755 e recusando0777. Uma
política explícita, privada e exclusiva de backup agora pode descrever a fonte
observada. Ela exige razão fixa `SteamOS_automount_chmod777`, modos exatos0777,
SHA do automounter instalado e SHA integral da raiz diagnosticada. O bootstrap
sela a política no snapshot root antes da execução. Outro modo, script ou
conteúdo de raiz aborta. O plano C80 não foi editado, nem o contador72.

UID/GID0, tipos/links, todos os outros pais, diretórios privados0700, modos
específicos das folhas, allowlist, identidade de rede/key/auth e contador
continuam estritos. As rotinas não tratam0777 como formato canônico de firmware:
recibo e confirmação independente propagam `metadata_repair_required_before_boot`.
Sem política explícita o coletor recusa recibos dessa fonte. A política também
é vinculada por hash no recibo e reconferida pela coleta do host.

O backup continua sendo somente leitura de payload. Guarda de identidade,
cache dos aliases, namespaces, swap/holders, fsck sem reparo, mount privado
`ro,noload,nosuid,nodev,noexec`, duplo inventário de userdata e hash final do
prefixo permanecem como [C81](phase4-offline-backup.md). A sincronização de
aliases pode concluir buffers pendentes; não é uma alegação de ausência total
de IO físico. O helper não altera modos no cartão.

## Verificação e resultado real

**86casos passaram**: os72 anteriores foram reexecutados porque o núcleo mudou,
com14 casos novos de política/root0777. Cobrem recusa padrão, aceitação somente
por política explícita, recusa de outro pai permissivo, fonte alterada, política
inválida e propagação da obrigação de reparo sem habilitar writer.17 testes de
transporte e11 do auditor passaram. Containers existentes sem rede/dispositivos,
sem instalação de dependências ou rebuild de SDK.

A cópia real parcial também passou por validação local dos seis arquivos
privados contra C80/boot72: o padrão recusou0777, a política explícita aceitou
a fonte exata, e a imagem permaneceu igual. Dados privados temporários foram
removidos. Nenhum conteúdo ou hash de folha privada aparece nos resumos públicos.

Usuário executou o helper revisado com sudo local. Ele criou
`/var/tmp/muos-r35s-c81-backup._nmzl6wx`, entregou folhas0400 ao usuário deck e
removeu o snapshot. Conferência independente no host aprovou:

- prefixo671.088.640bytes; FAT100MiB e raiz512MiB iguais às regiões da cópia;
- fsck.fat/e2fsck da FAT/raiz e e2fsck da p3 com retorno0, sem reparos;
- seis arquivos privados com identidade e contador iguais ao survey; seed
  offline recente preservado sem carregar ou gerar chave;
- nove arquivos de preferências/saves, USTAR61.440bytes, marcadores, modos,
  nomes e hashes verificados;
- prefixo final relido igual à primeira cópia; p3 desmontada;
- todos os arquivos e diretório da cópia independente sincronizados.

Survey posterior confirmou CID correto, nenhum mount do cartão e nenhum
snapshot root. A cópia do host foi tornada esparsa para conter uso do SSD;
tamanhos/hashes foram preservados e arquivos/diretório sincronizados novamente.
Isso não modifica bytes do backup. Não houve novo teste físico no R35S.

## Artefatos e próximo incremento

Todos sob `build/phase4/offline-backup`, privados:

- auditoria real `audit-native.u81m_f4b` e política de fonte;
- checks86 `checks.idd2hzax`, transporte17 `transport-checks.vocrj86t`;
- pacote `package.g1b5afk1`, deploy `deck-deploy.6lhz3fmv`;
- download completo `download.l9t_h7tc` e recibo host `native-copy.pojr1cyp`;
- survey final `deck-inspect.yhj_753v`.

Prova `dist/phase4/backup-native` contém fontes/casos/resumos e metadados dos
pais, sem plano privado, UUID live, hashes privados, ROM, chave, seed ou payload
de backup. Prova C81 anterior permanece congelada e intacta.

Próximo C83: contrato estreito para corrigir somente metadata das raízes p2/p3
para root:root0755, com backups/identidade/sem consumidores, antes/depois por
hashes e diferenças limitadas aos inodes/checksums. Isso é uma operação própria;
não usar o planner C80 como autorização genérica para escrever p3, nem o helper
C20 com comandos de formatação/restore. Prevenir novo automount que repetiria
o chmod. Depois implementar recuperação pósboot antes da migração C79.
Manter o cartão no Deck até preparar esse reparo. Original32 preservado.
