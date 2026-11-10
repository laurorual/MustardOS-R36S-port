# C102 — instalação aditiva do layout C100 no R35S

Data: 05/11/2026. Código próprio MIT. A fábrica C100 já foi validada offline;
este incremento aplica somente suas duas entradas novas ao cartão de teste
de128GB. O cartão original de32GB permanece separado. Não exige Steam Deck,
nova imagem completa ou novo provisionamento.

| Caminho | Antes | Depois |
| --- | --- | --- |
| /etc/asound.conf | Ausente |444bytes do template público existente, root:root0644/link único |
| /mnt/mmc | Ausente | Diretório vazio root:root0755/links2 |

O número de links de /mnt passa de2 para3. Os timestamps dos diretórios pais
mudam com as adições; não são alegados invariantes. O delta não substitui
arquivos existentes nem habilita caller, serviço, token.once ou autostart.

## Implementação e recuperação

`run-phase4-c79-layout-install.py` confere as provas C100/C99/C97 e reutiliza
as guardas C76/C77 já confrontadas com a árvore C79. Exige o mesmo boot/UUID
qualificado por C97, raiz ext4RO0755, cartão de teste/modelo/kernel corretos,
PCM fechado, p1/p3 desmontadas e nenhuma sessão ativa. Verifica os141arquivos
protegidos com seus metadados e também o template444bytes. Não repete o teste
de entropia C97, a sessão C99 ou a migração C94.

`prepare` só lê o console e sincroniza plano, registro de ausência, payload e
manifesto privados no host. `apply` cria uma única cápsula root0700 em /run,
confere o pacote, executa inspect sem escrita persistente e despacha uma única
vez. Um claim persistente no host impede redespacho após interrupção;
`collect` só observa a tentativa existente. Nenhum descritor de bloco é aberto.

O adaptador nativo usa o lock de sessão existente. Remonta a raizRW, cria um
arquivo temporário exclusivo em /etc, copia/confere os bytes, publica por
hardlink sem sobrescrever destino, retira o temporário e cria o diretório.
Confere o resultado, os hashes protegidos e o fingerprint privado, sincroniza
e remontaRO. O EXIT trap tenta recuperar falhas enquanto a raiz estiverRW e
sempre tenta selá-laRO, inclusive quando a recuperação precisa recusar algo.

A recuperação automática aceita somente entradas criadas por esta tentativa,
com bytes/modos/owner/links esperados; valida todas antes de remover alguma.
O caso intermediário de dois hardlinks exige o mesmo inode. Arquivo parcial,
alias, link extra, diretório com vizinho ou fundação alterada são preservados
para análise, sem repetição automática. Não há alegação de atomicidade entre
as duas entradas nem recuperação automática após perda de energia/SIGKILL.
Nesses casos, inspecionar o cartão/raiz antes de tentar outra operação.

O fingerprint cobre rede, seed, SSH, diagnóstico e preferências; permanece
somente na cápsula RAM. O host recebe apenas o sucesso da comparação, sem
conteúdo privado. Após sucesso, confere novamente os141arquivos e o layout,
PIDs/starttimes da infraestrutura, mountinfo global, PCM/rootRO/p1/p3 e retira
a cápsula. Recibos completos e identidade do boot ficam em build/, privados.

## Verificação offline

35casos passaram em `c79-layout-install/checks.7c3x0jfo`. A fixture roda em
container rootless sem rede/dispositivos/capabilities, sobre árvores de
diretórios descartáveis. Cobre instalação positiva; destinos e temporários
existentes/aliases; pais inválidos; /mnt não vazio; template alterado, com modo
incorreto ou hardlink; fundação alterada; falhas em guard/RW/staging/link/
publicação/diretório/verificação/sync/RO; retenção de cópia parcial, modos
alterados, hardlink estranho, alias e vizinho no novo diretório. Remounts e
guardas físicas são substituídos por callbacks nessa fixture; ela não equivale
a uma execução nativa do adaptador nem a um teste de queda de energia.

## Resultado nativo

Instalação aprovada em `c79-layout-install/install.s5gn_jxj`, no mesmo boot78,
em192.168.15.8. O plano e o registro de ausência foram sincronizados antes da
escrita. Inspect0, aplicação0 e todos os pós-checks0: arquivo444bytes root0644
com link único, diretório vazio root0755, raizRO0755,141arquivos protegidos e
template preservados. Fingerprint privado idêntico, PIDs/starttimes da rede
e mountinfo global idênticos; PCM fechado, p1/p3 desmontadas. Cápsula RAM
removida e saúde conferida novamente. Nenhum reboot ou teste de jogo realizado.

A primeira janela de espera do host terminou com a tentativa ainda ativa,
sem recibo. A inspeção mostrou raizRO e hashes em andamento. `collect` leu a
MESMA tentativa até concluir; não houve segundo despacho, nova escrita ou
repetição de instalação. O claim e os recibos privados preservam essa sequência.
Prova sanitizada em `dist/phase4/c79-layout-installed`, sem guardas privadas,
UUID real, fingerprint, chaves, seed, ROM, estado ou imagem.

## Próximo limite

Após qualificar a instalação, preparar um caller novo que use os caminhos
instalados diretamente. O contorno RAM C99 exige a ausência deles e não deve
ser repetido sem adaptação explícita. Reutilizar o caller original C77, sem
alterar suas fontes/provas históricas. Boot deste layout, autostart, navegador
geral de ROMs, novos saves, longa duração e energia permanecem etapas separadas.
