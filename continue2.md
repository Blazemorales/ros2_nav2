Aqui vai o resumo.

O que já foi feito

1. Diagnóstico inicial (já validado com você): o rover_nav2 que você imaginava não existia — o repo real já tinha um rover_navigation mais avançado (SmacHybrid/SmacLattice + RPP/TEB) e Gazebo Harmonic, mas faltava slam_toolbox, AMCL e explore_lite. Decidimos estender em vez de recriar.
2. Pacote novo rover_slam criado com:
   - config/slam_toolbox.yaml, config/amcl.yaml, config/explore_params.yaml
   - launch/slam.launch.py, launch/amcl.launch.py, launch/explore.launch.py
   - Toggle slam:=True/False para escolher entre mapear (slam_toolbox) ou localizar num mapa salvo (AMCL)
3. rover_gazebo/launch/gazebo.launch.py modificado para ligar tudo isso junto com o Nav2 existente, com argumentos slam, explore, map. Não mexi em serial.cpp/.hpp do rover_motor_controller_cpp, como pedido.
4. Dois bugs reais encontrados e corrigidos:
   - Conflito de dono do /map: o rover_localization original também subia o rtabmap (SLAM visual), que brigava com o slam_toolbox pelo map->odom. Corrigido: agora só sobe rgbd_odometry + ekf (odometria), não o rtabmap completo.
   - slam_toolbox nunca ativava: é um lifecycle node e meu launch inicial usava Node simples, então ele ficava parado em "unconfigured". Corrigido copiando o padrão configure→activate do launch oficial do slam_toolbox.
5. Processos zumbis: descobri que sobravam processos de testes anteriores (múltiplos robot_state_publisher/joint_state_publisher/bridges rodando ao mesmo tempo, de 3 execuções diferentes) brigando pelas mesmas tf/tópicos. Limpei tudo isso agora.

Problema atual (ainda não resolvido)

Depois de limpar os zumbis, o erro persistiu, então não era só sujeira de processo — é um bug real de nomenclatura de frame:

- O tópico /scan publica com frame_id: rover/base_link/lidar
- Mas essa frame não existe em lugar nenhum na árvore de tf — o link real do lidar no URDF se chama laser_link
- Isso faz o slam_toolbox descartar toda mensagem de scan ("dropping message... frame does not exist" / "timestamp earlier than transform cache"), então /map nunca fica completo e map->base_link nunca aparece

Causa raiz: o sensor lidar no hokuyo_frame_id> para forçar o Gazebo apublicar com o nome de frame correto (o sensor de câmera, no asus_xtion.urdf.xacro, já faz isso certo
via <optical_frame_id>camera_frame</stá sem o equivalente).

Próximo passo (ainda não aplicado)

Adicionar <gz_frame_id>laser_link</g> do lidar em hokuyo.urdf.xacro,rebuildar rover_description, testar de novo. Vou fazer isso agora.
