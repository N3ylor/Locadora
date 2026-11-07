% if locacoes:
    <div class="scroll">
        <table>
            <thead>
                <tr>
                    % if mostrar_cliente:
                    <th>Cliente</th>
                    % end
                    <th>Item</th>
                    <th>Retirada</th>
                    <th>Prevista</th>
                    <th>Situação</th>
                    <th class="num">Valor (R$)</th>
                    <th class="num">Multa (R$)</th>
                    <th class="num">Total (R$)</th>
                    % if devolver:
                    <th>Ação</th>
                    % end
                </tr>
            </thead>
            <tbody>
                % for loc in locacoes:
                <tr>
                    % if mostrar_cliente:
                    <td>{{loc.username}}</td>
                    % end
                    <td>{{loc.titulo}} <small>{{loc.tipo}} · {{loc.dias}} dia(s)</small></td>
                    <td>{{loc.data_locacao.strftime('%d/%m/%Y')}}</td>
                    <td>{{loc.data_prevista.strftime('%d/%m/%Y')}}</td>
                    <td>{{loc.situacao(hoje)}}</td>
                    <td class="num">{{loc.valor_fmt()}}</td>
                    <td class="num">{{loc.multa_fmt(hoje)}}</td>
                    <td class="num">{{loc.total_fmt(hoje)}}</td>
                    % if devolver:
                    <td>
                        <form method="post" action="/cliente/devolver/{{loc.id}}">
                            <button type="submit" class="small">Devolver</button>
                        </form>
                    </td>
                    % end
                </tr>
                % end
            </tbody>
        </table>
    </div>
% else:
    <p class="empty">{{vazio}}</p>
% end
