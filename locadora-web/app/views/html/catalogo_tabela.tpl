% if itens:
    <div class="scroll">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Título</th>
                    <th>{{rotulo}}</th>
                    <th class="num">Diária (R$)</th>
                </tr>
            </thead>
            <tbody>
                % for item in itens:
                <tr>
                    <td>{{item.id}}</td>
                    <td>{{item.titulo}}</td>
                    <td>{{item.categoria}}</td>
                    <td class="num">{{item.valor_formatado}}</td>
                </tr>
                % end
            </tbody>
        </table>
    </div>
% else:
    <p class="empty">{{vazio}}</p>
% end
