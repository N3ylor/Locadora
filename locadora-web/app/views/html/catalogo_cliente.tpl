% if itens:
    <div class="scroll">
        <table>
            <thead>
                <tr>
                    <th>Título</th>
                    <th>{{rotulo}}</th>
                    <th class="num">Diária (R$)</th>
                    <th>Alugar</th>
                </tr>
            </thead>
            <tbody>
                % for item in itens:
                <tr>
                    <td>{{item.titulo}}</td>
                    <td>{{item.categoria}}</td>
                    <td class="num">{{item.valor_formatado}}</td>
                    <td>
                        % if (tipo, item.id) in indisponiveis:
                            <span class="badge off">Alugado</span>
                        % elif not pode_alugar:
                            <span class="badge off">Limite atingido</span>
                        % else:
                            <form class="inline" method="post" action="/cliente/alugar">
                                <input type="hidden" name="tipo" value="{{tipo}}">
                                <input type="hidden" name="item_id" value="{{item.id}}">
                                <input type="number" name="dias" min="1" max="{{dias_max}}" value="3" required
                                       aria-label="Dias de locação de {{item.titulo}}">
                                <span class="unit">dias</span>
                                <button type="submit" class="small">Alugar</button>
                            </form>
                        % end
                    </td>
                </tr>
                % end
            </tbody>
        </table>
    </div>
% else:
    <p class="empty">{{vazio}}</p>
% end
