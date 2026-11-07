# C71 — transação seletiva do provider e consumidor

Preparação offline em 03/11/2026 para migrar os payloads públicos C62 para
provider C65 e host C67, qualificados juntos em RAM no C68. Este incremento
não instala arquivos no console e não grava a imagem completa C70.

O [preparador](../../port/scripts/prepare-phase4-provider-upgrade.py) confere
provas anteriores, hashes da receita/composição e aprovação física dos
componentes. O plano fixa cinco substituições (host e quatro bibliotecas),
26 folhas novas, 12 folhas antigas removidas e 29 diretórios novos. Retira
13 diretórios antigos vazios, pertencentes ao pacote C60. Retirar seus
metadados evita deixar manifestos que descrevem o host e as bibliotecas
anteriores. Não altera pais compartilhados, serviços, boot, core, conteúdo,
estado salvo, preferências, rede, seed, host keys ou contador.

O backup seletivo contém os 17 arquivos públicos originais e seus modos,
reconstituídos dos payloads locais aprovados. Sua correspondência com o
console deverá ser conferida antes de qualquer RW. Registra presença dos
13 diretórios antigos e ausência dos 29 novos. Backup, plano e tar são
sincronizados no host independentemente da cápsula RAM futura. Não é backup
integral do cartão nem promessa de recuperação após perda de energia.

A [transação MIT](../../port/device/rk-r35s-p0/provider-upgrade/transaction.sh)
usa uma política gerada de caminhos fixos, sem destinos fornecidos pelo
caller. Confere os modelos completos antes/depois, pais sem symlink,
owner/modos/link único, ausência de temporários e de vizinhos nas raízes de
metadados. Confere também 101 pré-requisitos preservados: fundação97 e
store4. O antigo instalador C62 permanece imutável e continua limitado a
adições; não foi adaptado silenciosamente para sobrescrever arquivos.

Depois da guarda externa/lock/remount, cria diretórios com journal, prepara
folhas vizinhas com noclobber e verifica hash/modo. Substituições usam rename
atômico por folha; adições usam publicação exclusiva. Só retira as folhas
obsoletas quando os novos arquivos já foram publicados, e exige diretórios
vazios para removê-los. A transação inteira não é atomicamente comutável.

Rollback valida todas as folhas e temporários existentes antes de restaurar
ou remover dados. Aceita apenas bytes/modos originais ou novos revisados;
conteúdo inesperado é preservado para inspeção. Recria os diretórios antigos,
restaura os 17 originais, remove adições reconhecidas e somente os novos
diretórios registrados. O adaptador nativo deverá tentar rollback e selar
RO mesmo quando a recuperação recusar conteúdo inesperado. Nenhum teste de
perda elétrica/crash entre syscalls foi realizado.

O [checker](../../port/scripts/check-phase4-provider-upgrade.py) exercita
140 casos em diretórios de fixture isolados, três containers simultâneos no
máximo: aplicação/rollback completo, falha em cada criação de diretório,
staging/publicação de folha, remoção de folha/diretório, guarda, RW, verify,
sync e RO. Também testa drift/hash/modos, hardlink/symlink, pais inseguros,
colisões, vizinhos, corrupção do payload/backup e especificações extras.
Os casos de conteúdo inesperado exigem preservação, em vez de declarar
restauração bem-sucedida. As fixtures usam os payloads públicos reais com
um sentinel sintético para a fundação; guardas de mídia e remounts reais
pertencem ao incremento nativo posterior.

Plano: `build/phase4/provider-upgrade/prepare.agnhn2y8`. Checks:
`build/phase4/provider-upgrade/checks.tvie8_8z`. A prova pública inclui
fontes/política/planos/recibos, sem ELF, tar de implantação ou payloads.
O backup executável continua em build, independente do aparelho.

Em paralelo, uma leitura de saúde para o futuro C72 confirmou o mesmo boot
71/UUID C68, raiz RO, payload C62 íntegro, fundação e quiescência. Ela não
autoriza inferir que esses fatos continuarão atuais: o executor fará nova
conferência e vínculo antes da implantação. Nenhuma escrita persistente no
console foi realizada nesta etapa; original32 e Steam Deck preservados.
