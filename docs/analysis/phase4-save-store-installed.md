# Fase 4 — C57: instalação seletiva do pacote de saves

Em 02/11/2026, os quatro arquivos do pacote C55 foram instalados no cartão de
teste de 128 GB e conferidos nativamente no R35S, C07/boot69. Nenhum arquivo
existente foi substituído. O CLI passou em uma prova curta com diretório
sintético em RAM; a raiz retornou a somente leitura e p3 ficou desmontada.
Não houve reboot, token C12/C25, serviço automático ou sessão de jogo.

## Escopo e procedência

Foram instalados somente:

- `/usr/libexec/muos-save-store/muos-save-store` (0755);
- `/usr/libexec/muos-save-store/payload.sha256` (0644);
- `/usr/share/muos-save-store/contract.json` (0644);
- `/usr/share/licenses/muos-save-store/LICENSE` (0644).

Três diretórios novos são root:root0755; as quatro folhas são root:root,
regulares e com um link. Os bytes vêm da releitura C56, com hashes ligados à
prova congelada C55. O ELF MIT permanece idêntico ao C52, SHA256
`e9540c40e00a9b46b3eee0efbb2a669bdc16f6721359a1fd2a1800836929056d`.
Zlib/glibc existentes foram preservadas. Não foi compilado ou instalado outro
ELF; o código original C52 e o store comercial C53/C54 não foram alterados.

Foram consultados o instalador e a transação C24/C36, inclusive suas guardas
de mídia, fingerprint privado, exclusão por lifetime lock e remount/rollback.
O C24 permite substituir arquivos e exige backup não vazio; o C57 tem
política separada e exata para quatro adições em diretórios ausentes, sem
ampliar a lista de destinos do instalador anterior. Todo código novo é MIT
em `port/device/rk-r35s-p0/save-store-install/` e `port/scripts/`.

## Plano, backup e aplicação

Stage final: `build/phase4/save-store-install/install.0kvv3gdl`.
`plan.json` registra boot69, ausência dos destinos e os quatro hashes/modos.
`absence-backup.json` é o backup desse estado anterior: **zero arquivos
originais copiados**, ausência dos três diretórios e folhas esperadas, com
regra de remoção seletiva. Não é backup de cartão inteiro. Os arquivos do
plano, recibo, manifesto e pacote de recuperação são fsynced no host antes de
permitir remount da raiz. A recuperação não depende da cápsula RAM do console.

O survey somente leitura confirmou guard CID/capacidade do cartão128,
PARTUUID/ext4 da raiz, kernel/modelo, rootRO0755, taint0, C07/boot69, áudio
fechado e ausência dos destinos. Pais existentes root:root0755 e sem symlinks.
A guarda recusa o original32 se encontrado. A fundação publicada permanece
com97 entradas, SHA256 do manifesto
`0b4967c9bd7f04f097374f29fc26fb880b6c360186fab2da24672f621591721f`.

Após payload público de70KiB transferido à RAM e hashes conferidos, o adapter
nativo obtém o lifetime lock e repete as guardas/ausência. A aplicação única
remonta somente a raiz em RW, cria três diretórios exclusivos e prepara cada
folha com noclobber. Publicação por hard link exclusivo nunca substitui um
destino concorrente; o temporário é removido e o link final conferido como1.
Manifesto, fundação e fingerprint privado devem coincidir antes de sync/remount
RO. O fingerprint de network/seed/SSH/contador fica somente na RAM remota;
nenhum desses bytes ou hashes privados é coletado pelo host.

O trap tenta rollback de qualquer aplicação parcial e sela a raiz em RO
mesmo se a recuperação precisar de inspeção. A recuperação valida todos os
arquivos publicados antes de remover algo; conteúdo inesperado é preservado.
O rollback explícito reenvia o pacote original, exige hashes/modos, guardas e
C07 saudável, e remove somente essas folhas e os três diretórios vazios.
Aceita contador posterior sem restaurar contador, seed ou credenciais antigos;
esse caminho não foi exercido fisicamente em um novo boot.

## Testes e problema encontrado

26 fixtures em container passaram: recusa por guarda, payload corrompido,
modo incorreto, caminho extra/vizinho, destino preexistente, symlinks de folha
ou pai e deriva da fundação; aplicação completa; rollback à ausência;
falha em cada um dos três diretórios e em cada uma das quatro preparações e
publicações; falha na verificação final/remount; preservação de conteúdo
inesperado no rollback; percurso de pais com `dirname` do BusyBox AArch64.
São provas do algoritmo em filesystem sintético, sem injetar falhas no cartão.

A primeira pré-inspeção nativa (`install.a4fy86sk`) encontrou um laço de
`dirname //`: BusyBox preserva `//`, enquanto GNU dirname usado pelas fixtures
iniciais normaliza `/`. O helper foi terminado por PID/comando exatos, antes
de qualquer remount ou despacho apply. RootRO e ausência do pacote foram
conferidos; a cápsula foi removida, com recibo de falha/limpeza preservado.
O percurso agora termina explicitamente em `/` ou `//`, e o caso adicional
roda a implementação real do BusyBox via A35/QEMU. Um novo plano e novas
fixtures precederam a instalação final; o pacote antigo não foi redisparado.

No ensaio final, inspect0/apply0, quatro hashes/modos/link counts válidos,
manifesto do pacote aprovado, fundação97 preservada. O CLI **instalado** criou
HEAD0 somente em `/run/muos-c57-probe.*/store`, com identidade sintética zero:
init0/status0 deram current0/previous0/next1; recover retornou3 pela ausência
de geração anterior. Isso exercita o caminho instalado e as dependências;
não repete ou substitui as34fixtures/laboratório ext4 C52 já aprovados.

RootRO, boot69, taint0, PCMclosed, quiescência, processos de infraestrutura
(PID/starttime) e mounts globais antes/depois coincidiram. P3 permaneceu
**desmontada durante todo C57**: nada leu ou escreveu o save comercial ou as
preferências55/70. Nenhum controle/mixer/DRM ou configuração de áudio foi
alterado. Diretório sintético, payload, auxiliares e fingerprint RAM foram
removidos; página de diagnóstico anterior permanece. Original32 e Steam Deck
não foram acessados. A imagem C56 não foi enviada ou gravada no cartão.

## Operação e provas

Sequência executada, com o estágio gerado pela preparação:

```sh
python3 port/scripts/run-phase4-save-store-install.py prepare --host 192.168.15.14
python3 port/scripts/check-phase4-save-store-install.py
python3 port/scripts/run-phase4-save-store-install.py apply \
  --host 192.168.15.14 --stage build/phase4/save-store-install/install.0kvv3gdl
python3 port/scripts/package-phase4-save-store-install.py
```

**Não repetir prepare/apply:** os diretórios agora existem. `verify` serve
para retomar uma aplicação pendente antes de remover sua cápsula; após a
conclusão, o script guardado `final-health.sh` contém as conferências somente
leitura, sem depender da cápsula já removida. O rollback, se necessário após
nova leitura de saúde, é:

```sh
python3 port/scripts/run-phase4-save-store-install.py rollback \
  --host IP_ATUAL --stage build/phase4/save-store-install/install.0kvv3gdl
```

Preservar o stage e seu `deployment.tar` para recuperação. O modo rollback usa
os bytes arquivados, mesmo que os scripts de trabalho evoluam. Não executar
rollback por rotina: isso retiraria o incremento instalado e aprovado.
A prova `dist/phase4/save-store-installed/SHA256SUMS` contém apenas fontes,
plano/recibos públicos, resultados e comandos, sem ELF, tar, ROM, estados,
PNG, PCM, credenciais ou fingerprint privado.

## Próximo incremento

C58: adaptar o diagnóstico de persistência para consumir o CLI instalado com
verificação do manifesto e hash aprovado, em vez de transportar outra cópia
executável em RAM. Manter o runtime e os estados intermediários em RAM,
identidade exata e p3RO por padrão; gravação durável continua apenas explícita.
Preparar fixtures de despacho/recusa antes de uma futura sessão supervisionada.
Não afrouxar C53/C54 ou repetir save/prepare comercial automaticamente.

Nenhum C58 armado. Integração permanente do frontend, boot da imagem C56,
novo boot do pacote instalado, perda elétrica, Power/suspend, SRAM/GC,
continuidade de áudio e performance NES permanecem fora deste ensaio.
