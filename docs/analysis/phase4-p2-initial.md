# C94 — entrada finita para migração inicial C79

Data: 05/11/2026. Código próprio MIT. Reutiliza os contratos C84–C93 e o
controlador C87/C90, sem alterar as fontes ou provas anteriores. As referências
upstream permanecem somente leitura; esta etapa não copia novo código delas.

O C94 prepara a instalação da árvore pública C79 na p2 do test128. A entrada
`phase4-p2-initial.py migrate` é separada de `phase4-p2-recover.py recover`.
O hash da fábrica pública C79 está fixado no novo helper. A candidata precisa
conter o estado privado atualizado, um seed novo sem crédito e um contador
reservado, derivados da captura física atual. Não usar a candidata C88 com
estado72 nem o snapshot C86 antigo73.

## Contrato da operação

1. C93 exige o fence existente da recuperação C89, sua cópia independente e
   o primeiro boot pós-recuperação qualificado. O C94 verifica novamente os
   hashes desses registros e o caminho de entropy sem crédito. Uma captura
   mais recente pode ter contador maior, inclusive após reboot do usuário.
2. O preparador revalida a composição C92/C93, os checks atuais, provas
   anteriores, kernel qualificado, identidade do cartão, automount guard e
   quatro aliases somente leitura. Um claim persistente exclusivo impede
   repetir transferências automaticamente após interrupção.
3. Dois receivers finitos transferem fábrica e candidata para arquivos
   privados regulares no SSD do Deck, com hash do stream e releitura completa,
   escrita esparsa, criação exclusiva e fsync. Não recebem caminhos de cartão.
4. O pacote de 19 folhas verificadas é copiado para `/run` root:root0700;
   folhas0400, sem links, limitadas a1MiB. O helper executa com ambiente limpo,
   valida esquema/operação/roles e abre namespace privado de montagem.
5. A operação confere o backup remoto independente e copia as duas imagens
   para um estágio root privado persistente fora do cartão. A captura C86 é
   refeita somente leitura, exigindo o mesmo hash da p2 usado na composição.
6. Antes de liberar escrita, o callback C93 deriva a elegibilidade de três
   scans por descritores: fábrica, snapshot recém-capturado e candidata. Confere
   árvore pública, identidade, históricos, atributos, seeds, contador e hashes
   novamente. O controlador fixo mantém as guardas de identidade, aliases,
   exclusividade e preservação integral do complemento da p2.
7. O controlador escreve exatamente512MiB na p2, sem repetição após erro ou
   escrita curta; faz fsync, releitura fria e restaura quatro aliases RO.
   MBR/p1/p3 ficam fora do intervalo de escrita e são comparados integralmente.
   São as mesmas cinco passagens completas já qualificadas no C89, com leitura
   total próxima de596GiB; o ensaio físico pode durar mais de uma hora.
8. Somente após escrita verificada, sela o próximo fence C84 e publica o
   recibo. O coletor confere journal, extent, fontes, captura, proteções e uma
   cópia independente do novo fence no host. Até então o cartão fica offline.

`phase4-p2-recover.py` fornece apenas os utilitários de cópia privada e
conferência de backup; seu modo privilegiado nunca é chamado pelo C94.
O coletor reutiliza somente o validador puro de journal/extent/fence do C89,
adaptando nomes em dicionários locais. Esses dicionários não chegam ao writer
nem à elegibilidade da recuperação. O monitor reutiliza a máquina de estados
do observador anterior, com caminhos finitos C94, e só coleta uma vez. Não
inicia, encerra ou repete o gravador.

Qualquer falha conserva estágio/snapshot/journal. A operação tenta reforçar
RO e publica relatório privado; falhas não autorizam retry ou rollback.
O recibo nativo e a prova mantêm `boot_handoff_authorized=false` e
`physical_boot_after_initial_migration_qualified=false`. A prova nativa só
poderá ser publicada depois da coleta independente; o boot será outra etapa.

## Verificação offline

`check-phase4-p2-initial.py entry|transport` usa o container já existente,
sem rede, sem dispositivos, rootfs somente leitura e capabilities removidas.
As imagens ext4 sintéticas são32MiB, com árvores públicas antiga/nova distintas,
identidade e histórico fictícios. Os receivers usam streams sintéticos4MiB;
o tamanho de produção continua fixo512MiB.

- Entrada:43casos. Esquemas e roles finitos, fábrica pinada, contadores,
  backup/lineage/hash inválidos, boot sem qualificação, pacote extra/alterado,
  modos/links/limite, snapshot protegido e execução com ambiente limpo.
  O corpo da transação executa composição/scans reais e cópias privadas,
  com somente o cartão/controlador físico e backup remoto substituídos.
  Deriva contador76/primeiroC07=77; callback termina antes da escrita simulada,
  fence surge depois. Falhas de backup/captura/contador/escrita/fence impedem
  conclusão e preservam os arquivos de entrada.
- Transporte:41casos. Gate de composição/captura/fence/counter, recusa antes
  de SSH, receivers regulares com hash/releitura/fsync e streams inválidos,
  recibos/journal/extent/fence e observador sem repetição. O teste não executa
  os mains positivos completos de deployment/coleta nativa/publicação nativa.

As imagens sintéticas são removidas após os logs. As fontes e provas ancestrais
são conferidas por hash. A prova `dist/phase4/p2-initial-prepared` contém apenas
fontes, testes e relatório sanitizado. Nenhum seed/ROM/snapshot de produção é
exportado. Compilação/import/teste não equivale a qualificação física.

## Próxima execução física

Manter o test128 no R35S até confirmar estado real e solicitar desligamento
normal. A transferência ao Deck depende de confirmação de desligamento total;
original32 permanece guardado. O Deck continua necessário, portanto seus
backups, fence e ferramentas não devem ser limpos agora.

No Deck será necessária uma nova captura C86 `postboot`, vinculada ao fence
EXISTENTE de `p2-recovery/latest-complete-recover` (contador74), não um fence
inventado. O helper C86 é executado pelo usuário no Konsole com sudo local;
o SSH não tem sudo sem senha. Depois de coleta/scan independente:

```sh
python3 port/scripts/prepare-phase4-initial-migration.py compose
python3 port/scripts/prepare-phase4-p2-initial.py --host IP_DO_DECK
```

O último comando imprime o caminho exato do pacote e o comando sudo local.
O writer `migrate` só será solicitado após confirmar composição, pacote e
readiness reais. Durante a execução, o observador aceita apenas o diretório
persistente e nome root-helper exatos já existentes. Não repetir comandos
após erro/interrupção sem inspecionar os registros.

```sh
python3 port/scripts/watch-phase4-p2-initial.py --host IP_DO_DECK \
  --result /var/tmp/muos-r35s-c94-initial.XXXXXXXX \
  --root-helper muos-r35s-c94.XXXXXXXX
```

Ainda não houve composição de produção, deployment, seed de produção novo,
escrita física ou boot C79 nesta etapa. A captura antiga disponível é
intencionalmente recusada antes de qualquer transferência ou geração de seed.
