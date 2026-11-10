# Fase 4 — C62: instalação seletiva do host muxretro

Em 03/11/2026, os treze arquivos do pacote C60 foram instalados no cartão de
teste de128GB, no R35S/C07/boot70/IP192.168.15.14. Nenhum arquivo existente
foi substituído. O ELF instalado passou `--version`/`--help` com resolução
eager das bibliotecas. A raiz retornou a somente leitura, p3 permaneceu
desmontada e nenhuma sessão gráfica, serviço, save ou reboot foi iniciado.

## Escopo, origem e contrato runtime

A receita C60, suas macros de instalação e o hook `pkg-generic.mk` do
Buildroot da bancada foram conferidos, junto da transação/adaptador C57 e
dos scripts runtime C53/C61. O C57 supõe quatro folhas dentro de três
diretórios novos; C62 precisa lidar também com a folha em um pai compartilhado
e treze diretórios aninhados. Por isso usa política própria, sem ampliar a
lista de destinos ou alterar as provas do instalador anterior.

O código novo MIT está em `port/device/rk-r35s-p0/muxretro-install/` e nos
scripts `run/check/package-phase4-muxretro-install.py`. A origem é o payload
C60 de `build/phase4/muxretro-package/build.mdou4mqr/target`, vinculado às
provas C60 e C61 e à confirmação física C61. Os treze destinos são:

- `/opt/muos/frontend/muxretro`,0755;
- `/usr/share/muos-muxretro/{payload.sha256,platform.sha256,provenance.json}`,
  0644;
- nove avisos de licença sob `/usr/share/licenses/muos-muxretro/`,0644.

As treze folhas são regulares, root:root e com um link; os treze diretórios
novos são root:root0755. O manifesto instalado cobre as outras doze folhas.
ELF, licenças e metadados são byte-idênticos ao pacote C60. O host conserva
SHA256 `8d519958cdb1ae599e2b2af2f6ee90053bca1a83cce0380baa3a1d7150983f05`.
Nenhuma biblioteca de plataforma foi substituída ou acrescentada.

O plano mantém ativação manual e explicita a dependência C46 do diagnóstico:
`libmuxmod.so` RAM fixada em
`1ec8acd906ee25bd83b59c0c5818e7310d62bfeaabadb2b473e03562d7d6bcc9`.
Ela **não foi instalada**. Precisando o escopo por componente: o worker C53
exporta a ordem padrão `/opt/muos/frontend/lib`; `select.sh` aplica o override
C46 especificamente às aberturas do `muxfrontend` para selecionar e retornar.
A chamada posterior de `app-launch.sh` herda a ordem padrão do worker.
O probe ABI C61 também exercitou o host com o override, mas isso não significa
que todo processo da sessão o herdou. C62 testa a CLI instalada com as
bibliotecas da fundação; não promove um novo fluxo gráfico sem a seleção C46.

Instalar esses arquivos não habilita menu permanente, chamadas de core,
writer, ROM, save, service, token C12/C25 ou boot automático. A integração do
provider completo de bibliotecas continua pendente. As restrições da imagem
gráfica privada e os warnings registrados no C60 continuam válidos.

## Plano, backup e publicação

Stage de recuperação:
`build/phase4/muxretro-install/install.67io22z3`.

O survey somente leitura confirmou cartão128/CID/capacidade, kernel/modelo,
PARTUUID/ext4, rootRO0755/taint0, C07/boot70/rede e PCM fechado. Os pais
compartilhados foram conferidos root:root0755 e sem symlinks. Confirmou
ausência do host e das duas raízes novas de metadados/licenças, inclusive
colisões de temporários. O original32 é recusado pelas guardas existentes.

`plan.json` fixa destinos, hashes/modos, boot, escopo runtime e105
pré-requisitos públicos: fundação97, quatro bibliotecas de link C60 e quatro
arquivos C57. O manifesto publicado da fundação permanece com97 entradas;
o arquivo105 é apenas uma guarda adicional desta implantação. A existência,
os hashes e os avisos de licença do pacote C60 foram conferidos antes do plano.

`absence-backup.json` registra ausência dos treze destinos e diretórios:
**zero arquivos originais copiados**. É um backup seletivo de ausência,
não uma imagem do cartão. Plano, recibo, manifesto e `deployment.tar`
foram fsynced no host antes de permitir o remount. A recuperação independe
da cápsula volátil do console. O arquivo público de1.792.000bytes foi enviado
à RAM e conferido antes de extrair/inspecionar.

O adaptador obtém o lifetime lock, repete mídia/quiescência/ausência/schema/
pré-requisitos e só então remonta a raiz RW. Cria diretórios exclusivos em
ordem de pais, registrando os criados. Prepara cada folha com noclobber e
publica por hard link exclusivo; não substitui um destino concorrente.
O temporário é retirado, e o link final1/hash/modo é conferido. Depois de
verificar todos os arquivos, diretórios, pré-requisitos e fingerprint privado,
faz sync e remount RO.

O fingerprint de network/seed/SSH/contador é calculado e comparado apenas
na RAM remota; nem seus bytes nem seu hash são coletados. Os arquivos e
fingerprints temporários foram removidos após o sucesso.

## Rollback e testes

O trap tenta recuperar qualquer aplicação parcial e sela a raiz em RO.
Rollback valida antes todas as folhas e temporários presentes, além do layout
das duas raízes novas. Conteúdo/modo inesperado, symlink, vizinho novo ou
temporário incompleto é preservado para inspeção. Não há promessa de apagar
automaticamente dados que deixaram de corresponder ao payload.

Diretórios só são removidos se constarem do journal de criação, em ordem
inversa. A recuperação explícita de uma instalação completa reenvia os
bytes arquivados, valida todos os destinos e então adota a lista exata de
diretórios. Ela nunca retira o pai compartilhado `/opt/muos/frontend` nem
seus outros arquivos. Pode aceitar boot posterior pela guarda de contador,
sem restaurar contador, seed ou credenciais antigos; não foi exercida
fisicamente em outro boot.

Passaram61fixtures em container sem rede, usando filesystem sintético:

- recusa por guarda, hash/modo incorreto, caminho extra/vizinho, destino
  preexistente, symlink de folha/pai e deriva da fundação;
- aplicação completa e rollback exato à ausência;
- falha em cada uma das13criações de diretório,13preparações e13publicações;
- falhas de verificação/remount e recuperação;
- preservação de conteúdo inesperado, diretório vizinho vazio, temporário
  corrompido, pai compartilhado e arquivo irmão;
- recusa por modo inseguro do pai ou temporário preexistente;
- percurso real de pais com dirname BusyBox AArch64 via A35/QEMU, incluindo
  `//`, sem repetir o erro antigo do C57.

O warning de checksum no stderr das fixtures pertence à injeção deliberada
de corrupção. Não houve falha intermediária no ensaio nativo, nem injeção
de falhas ou rollback no cartão. Nenhuma dependência foi instalada no host.

## Resultado nativo e operação

Inspect0/apply0, treze hashes/modos/links e treze diretórios válidos; os105
pré-requisitos e manifesto do pacote/store conferidos. O host **instalado**
respondeu `muxretro interface 1` e mostrou seu help sob `LD_BIND_NOW=1`.
Não iniciou engine, conteúdo ou gráficos; a confirmação física C61 não foi
repetida por rotina nem atribuída automaticamente ao novo caminho instalado.

RootRO, boot70, PCMclosed/taint0, infraestrutura PID/starttime e mounts
globais coincidiram antes/depois. P3 ficou desmontada durante todo C62;
preferências55/70 e store comercial geração1/HEAD1/0/2 não foram montados
nem alterados. Não houve alteração de mixer/DRM/volume/áudio. A cápsula RAM
foi removida; a página diagnóstica C61 anterior permanece. Original32 e
Steam Deck não foram acessados, e nenhuma imagem foi enviada/regravada.

Sequência concluída:

```sh
python3 port/scripts/run-phase4-muxretro-install.py prepare --host 192.168.15.14
python3 port/scripts/check-phase4-muxretro-install.py
python3 port/scripts/run-phase4-muxretro-install.py apply \
  --host 192.168.15.14 --stage build/phase4/muxretro-install/install.67io22z3
python3 port/scripts/package-phase4-muxretro-install.py
```

Não repetir prepare/apply: os destinos agora existem. `verify` serve apenas
para retomar a coleta de uma aplicação pendente com cápsula existente. Para
uma conferência posterior, `final-health.sh` é somente leitura e independe da
cápsula removida, mas fixa o contador do plano; avaliar um novo boot em um
incremento próprio. Não reaplicar o teste negativo C61 que exige host ausente.

Se uma recuperação explícita for necessária, após reler saúde/mídia:

```sh
python3 port/scripts/run-phase4-muxretro-install.py rollback \
  --host IP_ATUAL --stage build/phase4/muxretro-install/install.67io22z3
```

Preservar esse stage e o tar; não fazer rollback por rotina, pois removeria
o incremento instalado. Prova `dist/phase4/muxretro-installed/SHA256SUMS`
contém fontes, plano, recibos e testes; exclui ELF, tar, ROM, estado, PNG,
PCM e fingerprint/credenciais privados. Provas C60/C61/C57 e `.config`
compartilhado do SDK foram conferidos intactos.

Próximo C63: adaptar o diagnóstico para consumir o host instalado com
manifesto/hash/modos/pais fixados, sem transferir outra cópia ELF ou criar
fallback. Preservar seleção C46 em RAM, CLI C57/load-only e rootRO; preparar
recusas/vínculo de boot próprios antes de uma sessão supervisionada de
restauração/saída. Nada armado. GUI pelo caminho instalado, novo boot do
pacote, frontend permanente, boot da imagem, Power/suspend, SRAM/GC/perda
elétrica e áudio contínuo permanecem fora da qualificação C62.
