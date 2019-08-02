import logging

import plugins.adversary.app.config as config
from plugins.adversary.app.service.adversary_api import AdversaryApi
from plugins.adversary.app.service.api_logic import ApiLogic
from plugins.adversary.app.service.background import BackgroundTasks

name = 'Adversary'
description = 'Adds the full Adversary mode, including REST and GUI components'
address = '/plugin/adversary/gui'


async def setup_routes_and_services(app, services):
    await services.get('data_svc').reload_database(schema='plugins/adversary/conf/adversary.sql')

    auth_svc = services.get('auth_svc')
    api_logic = ApiLogic(config.settings.dao, services.get('data_svc').dao)
    background = BackgroundTasks(api_logic=api_logic)
    adversary_api = AdversaryApi(api_logic=api_logic, auth_key=config.settings.auth_key, auth_svc=auth_svc)

    app.on_startup.append(background.tasks)
    # Open Human Endpoints
    app.router.add_static('/adversary', config.settings.plugin_root / 'static/', append_version=True)
    app.router.add_route('GET', '/conf.yml', adversary_api.render_conf)

    # Authorized Human Endpoints
    app.router.add_route('*', '/plugin/adversary/gui', adversary_api.planner)
    app.router.add_route('*', '/adversary', adversary_api.planner)
    app.router.add_route('POST', '/operation/refresh', adversary_api.refresh)
    app.router.add_route('POST', '/operation', adversary_api.start_operation)
    app.router.add_route('*', '/operation/logs/plan', adversary_api.download_logs)
    app.router.add_route('*', '/operation/logs/bsf', adversary_api.download_bsf)
    app.router.add_route('*', '/operation/logs/operation', adversary_api.download_operation)
    app.router.add_route('POST', '/terminate', adversary_api.rebuild_database)
    app.router.add_route('*', '/settings', adversary_api.settings)
    app.router.add_route('*', '/cagent', adversary_api.cagent)

    app.router.add_route('POST', '/op/control', adversary_api.control)

    # Open Agent Endpoints
    app.router.add_route('GET', '/commander', adversary_api.rat_download)
    app.router.add_route('GET', '/deflate_token', adversary_api.deflate_token)
    app.router.add_route('GET', '/macro/{macro}', adversary_api.rat_query_macro)
    app.router.add_route('POST', '/login', adversary_api.rat_login)

    # Authorized Agent Endpoints (Agents use separate tokens & auth is implemented separately in the plugin)
    app.router.add_route('GET', '/api/heartbeat', adversary_api.rat_heartbeat)
    app.router.add_route('GET', '/api/jobs', adversary_api.rat_get_jobs)
    app.router.add_route('GET', '/api/jobs/{job}', adversary_api.rat_get_job)
    app.router.add_route('POST', '/api/clients', adversary_api.rat_clients_checkin)
    app.router.add_route('PUT', '/api/jobs/{job}', adversary_api.rat_get_job)
    return app


async def initialize(app, services):
    logging.getLogger('app.engine.database').setLevel(logging.INFO)
    config.initialize_settings(config_path='plugins/adversary/conf/config.ini', filestore_path='plugins/adversary/payloads')
    await setup_routes_and_services(app, services)
