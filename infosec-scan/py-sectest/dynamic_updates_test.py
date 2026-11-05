from scsession import SaltcornSession
from dynamic_updates_client import DynamicUpdatesClient;
import socketio
import time

adminEmail='admin@foo.com'
adminPassword='AhGGr6rhu45'

staffEmail='staff@foo.com'
staffPassword='ghrarhr54hg'

userEmail='user@foo.com'
userPassword='GFeggwrwq45fjn'

class Test:
  def setup_class(self):
    SaltcornSession.reset_to_fixtures()
    self.sess = SaltcornSession(port=3001)

  def teardown_class(self):
    self.sess.close()

  def test_connect(self):
    client = DynamicUpdatesClient()
    client.login(email=adminEmail, password=adminPassword)
    client.connect()
    assert client.sio.connected
    client.sio.disconnect()

  def test_join_dynamic_updates_room(self):
    client = DynamicUpdatesClient()
    client.login(email=adminEmail, password=adminPassword)
    client.connect()
    client.join_dynamic_updates_room()
    time.sleep(1)

  def test_run_trigger_admin(self):
    client = DynamicUpdatesClient()
    client.login(email=adminEmail, password=adminPassword)
    client.connect()
    client.join_dynamic_updates_room()
    client.run_trigger("emit_to_admin")
    time.sleep(1)
    assert len(client.updates) == 1
    client.run_trigger("emit_to_staff")
    time.sleep(1)
    assert len(client.updates) == 1
    client.run_trigger("emit_to_admin_and_staff")
    time.sleep(1)
    assert len(client.updates) == 2
    client.run_trigger("emit_tenant_wide")
    time.sleep(1)
    assert len(client.updates) == 3

  def test_run_trigger_staff(self):
    client = DynamicUpdatesClient()
    client.login(email=staffEmail, password=staffPassword)
    client.connect()
    client.join_dynamic_updates_room()
    client.run_trigger("emit_to_admin")
    time.sleep(1)
    assert len(client.updates) == 0
    client.run_trigger("emit_to_staff")
    time.sleep(1)
    assert len(client.updates) == 1
    client.run_trigger("emit_to_admin_and_staff")
    time.sleep(1)
    assert len(client.updates) == 2
    client.run_trigger("emit_tenant_wide")
    time.sleep(1)
    assert len(client.updates) == 3

  def test_connect_public(self):
    client = DynamicUpdatesClient()
    client.connect_as_public()
    assert client.sio.connected
    client.sio.disconnect()

  def test_join_dynamic_updates_room_public(self):
    client = DynamicUpdatesClient()
    client.connect_as_public()
    client.join_dynamic_updates_room()
    time.sleep(1)

  def test_run_trigger_public(self):
    public_client = DynamicUpdatesClient()
    public_client.connect_as_public()
    public_client.join_dynamic_updates_room()
    time.sleep(0.5)  # wait for room join to complete

    # public session can't call trigger API — use a logged-in client to fire triggers
    admin_client = DynamicUpdatesClient()
    admin_client.login(email=adminEmail, password=adminPassword)

    admin_client.run_trigger("emit_to_admin")
    time.sleep(1)
    assert len(public_client.updates) == 0
    admin_client.run_trigger("emit_to_staff")
    time.sleep(1)
    assert len(public_client.updates) == 0
    admin_client.run_trigger("emit_to_admin_and_staff")
    time.sleep(1)
    assert len(public_client.updates) == 0
    admin_client.run_trigger("emit_to_public")
    time.sleep(1)
    assert len(public_client.updates) == 1

  def test_broadcast_reaches_multiple_public_clients(self):
    # Both public clients join with distinct page_load_tags; broadcast reaches both
    client_a = DynamicUpdatesClient()
    client_a.connect_as_public()
    client_a.join_dynamic_updates_room()

    client_b = DynamicUpdatesClient()
    client_b.connect_as_public()
    client_b.join_dynamic_updates_room()
    time.sleep(0.5)

    assert client_a.page_load_tag != client_b.page_load_tag

    admin_client = DynamicUpdatesClient()
    admin_client.login(email=adminEmail, password=adminPassword)
    admin_client.run_trigger("emit_to_public")
    time.sleep(1)
    assert len(client_a.updates) == 1
    assert len(client_b.updates) == 1
    client_a.sio.disconnect()
    client_b.sio.disconnect()

  def test_public_clients_receive_page_load_tag_in_emit(self):
    # Server broadcasts to all public clients; each client receives the page_load_tag
    # that was sent with the triggering request so client-side filtering can work.
    client_a = DynamicUpdatesClient()
    client_a.connect_as_public()
    client_a.join_dynamic_updates_room()

    client_b = DynamicUpdatesClient()
    client_b.connect_as_public()
    client_b.join_dynamic_updates_room()
    time.sleep(0.5)

    assert client_a.page_load_tag != client_b.page_load_tag

    admin_client = DynamicUpdatesClient()
    admin_client.login(email=adminEmail, password=adminPassword)
    # Fire trigger tagged with client_a's page_load_tag
    admin_client.run_trigger("emit_to_public", page_load_tag=client_a.page_load_tag)
    time.sleep(1)

    # Both clients receive the emit (server does not filter by page_load_tag)
    assert len(client_a.updates) == 1
    assert len(client_b.updates) == 1

    # The emitted data carries the page_load_tag so each client can filter client-side
    received_tag = client_a.updates[0].get("page_load_tag")
    assert received_tag == client_a.page_load_tag
    assert received_tag != client_b.page_load_tag

    client_a.sio.disconnect()
    client_b.sio.disconnect()

  def test_run_trigger_user(self):
    client = DynamicUpdatesClient()
    client.login(email=userEmail, password=userPassword)
    client.connect()
    client.join_dynamic_updates_room()
    client.run_trigger("emit_to_admin")
    time.sleep(1)
    assert len(client.updates) == 0
    client.run_trigger("emit_to_staff")
    time.sleep(1)
    assert len(client.updates) == 0
    client.run_trigger("emit_to_admin_and_staff")
    time.sleep(1)
    assert len(client.updates) == 0
    client.run_trigger("emit_tenant_wide")
    time.sleep(1)
    assert len(client.updates) == 1

  # ── Security tests for GHSA-23w3-vxv3-xm92 ─────────────────────────────────
  # Before the fix, successAsyncHandler and workflowRunPromiseHandler passed
  # userIds = req.user ? undefined : null, which caused dynamic-update events
  # to broadcast to all authenticated sockets via the shared tenant-wide room
  # _${tenant}_dynamic_update_room.  The fix routes each event only to the
  # requesting user's per-user room _${tenant}:${user.id}_dynamic_update_room.
  # The emit_to_admin / emit_to_staff fixtures call emit_to_client(data, userId)
  # directly and validate the same per-user isolation property.
  # ────────────────────────────────────────────────────────────────────────────

  def test_idor_attacker_does_not_receive_other_users_dynamic_updates(self):
    """
    GHSA-23w3-vxv3-xm92: a socket joined to the dynamic-update room must not
    receive events targeted at a different user.
    Before the fix every authenticated socket subscribed to the tenant-wide room
    so any connected client silently received all per-user payloads.
    """
    attacker = DynamicUpdatesClient()
    attacker.login(email=userEmail, password=userPassword)
    attacker.connect()
    attacker.join_dynamic_updates_room()
    time.sleep(0.5)

    # emit_to_admin targets user_id=1 (admin); attacker is a regular user
    trigger = DynamicUpdatesClient()
    trigger.login(email=adminEmail, password=adminPassword)
    trigger.run_trigger("emit_to_admin")
    time.sleep(1)

    assert len(attacker.updates) == 0, (
      "IDOR: regular user received a dynamic-update event intended for the "
      "admin user via the shared tenant-wide room"
    )
    attacker.sio.disconnect()

  def test_cross_user_dynamic_update_isolation(self):
    """
    Bidirectional isolation: admin's targeted update must not reach the user
    socket, and a staff-targeted update must not reach either admin or user.
    """
    admin_client = DynamicUpdatesClient()
    admin_client.login(email=adminEmail, password=adminPassword)
    admin_client.connect()
    admin_client.join_dynamic_updates_room()

    user_client = DynamicUpdatesClient()
    user_client.login(email=userEmail, password=userPassword)
    user_client.connect()
    user_client.join_dynamic_updates_room()
    time.sleep(0.5)

    trigger = DynamicUpdatesClient()
    trigger.login(email=adminEmail, password=adminPassword)

    # emit_to_admin targets user_id=1 — only admin_client should receive it
    trigger.run_trigger("emit_to_admin")
    time.sleep(1)
    assert len(admin_client.updates) == 1, "Admin must receive its own targeted event"
    assert len(user_client.updates) == 0, (
      "IDOR: user received a dynamic-update event intended for admin"
    )

    # emit_to_staff targets user_id=2 — neither admin nor user should receive it
    trigger.run_trigger("emit_to_staff")
    time.sleep(1)
    assert len(admin_client.updates) == 1, (
      "Admin must not receive an event targeted at staff"
    )
    assert len(user_client.updates) == 0, (
      "User must not receive an event targeted at staff"
    )

    admin_client.sio.disconnect()
    user_client.sio.disconnect()

  def test_authenticated_user_receives_own_dynamic_updates(self):
    """
    Positive case: per-user rooms still deliver events to the correct recipient
    now that per-user events are scoped to _${tenant}:${user.id}_dynamic_update_room.
    """
    admin_client = DynamicUpdatesClient()
    admin_client.login(email=adminEmail, password=adminPassword)
    admin_client.connect()
    admin_client.join_dynamic_updates_room()
    time.sleep(0.5)

    admin_client.run_trigger("emit_to_admin")
    time.sleep(1)
    assert len(admin_client.updates) == 1, (
      "Admin must still receive its own targeted dynamic-update event"
    )
    admin_client.sio.disconnect()
