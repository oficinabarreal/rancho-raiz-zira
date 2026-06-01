"""
Tests exhaustivos del Simulador CRM — escenarios, pasos y formato.
Adaptado a la API real de crm_simulator.
"""
import unittest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulators.crm_simulator import SCENARIOS, Scenario, ScenarioStep


class TestSimulatorScenarios(unittest.TestCase):
    """Pruebas sobre los 8 escenarios del simulador."""

    def test_scenarios_count(self):
        """Deben existir 8 escenarios precargados."""
        self.assertGreaterEqual(len(SCENARIOS), 8,
                                f"Se esperaban >=8 escenarios, hay {len(SCENARIOS)}")

    def test_all_scenarios_have_ids(self):
        """Cada escenario debe tener un id único."""
        ids = [s.id for s in SCENARIOS]
        self.assertEqual(len(ids), len(set(ids)),
                         "Todos los escenarios deben tener IDs únicos")

    def test_all_scenarios_have_steps(self):
        """Cada escenario debe tener al menos 1 paso."""
        for s in SCENARIOS:
            self.assertGreater(len(s.steps), 0,
                               f"Escenario '{s.id}' debe tener steps")

    def test_scenario_step_structure(self):
        """Valida la estructura de cada paso (stage, action, detail)."""
        for scenario in SCENARIOS:
            for i, step in enumerate(scenario.steps):
                self.assertIsNotNone(step.stage, f"Step {i} de '{scenario.id}' debe tener stage")
                self.assertIsInstance(step.stage, str)
                self.assertIsNotNone(step.action, f"Step {i} de '{scenario.id}' debe tener action")
                self.assertIsInstance(step.action, str)
                # detail puede ser string vacío pero debe existir
                self.assertIsNotNone(step.detail, f"Step {i} de '{scenario.id}' debe tener detail")

    def test_all_scenarios_have_summary_and_channel(self):
        """Cada escenario debe tener summary y channel."""
        for s in SCENARIOS:
            self.assertTrue(len(s.summary) > 0, f"Scenario '{s.id}' debe tener summary")
            self.assertTrue(len(s.channel) > 0, f"Scenario '{s.id}' debe tener channel")
            self.assertTrue(len(s.source) > 0, f"Scenario '{s.id}' debe tener source")


class TestSimulatorDataIntegrity(unittest.TestCase):
    """Pruebas de integridad de datos del simulador."""

    def test_no_empty_details(self):
        """Ningún step debe tener detail completamente vacío (None)."""
        for scenario in SCENARIOS:
            for step in scenario.steps:
                self.assertIsNotNone(step.detail,
                                     f"Step detail vacío en '{scenario.id}'")

    def test_telegram_list_not_empty(self):
        """Cada escenario debe tener al menos 1 template de Telegram."""
        for s in SCENARIOS:
            self.assertGreater(len(s.telegram), 0,
                               f"Scenario '{s.id}' debe tener templates Telegram")

    def test_voice_exists(self):
        """Cada escenario debe tener voice en ES."""
        for s in SCENARIOS:
            self.assertTrue(len(s.voice_es) > 0,
                            f"Scenario '{s.id}' debe tener voice_es")

    def test_next_actions_defined(self):
        """Cada escenario debe definir next_actions."""
        for s in SCENARIOS:
            self.assertGreater(len(s.next_actions), 0,
                               f"Scenario '{s.id}' debe tener next_actions")

    def test_scenario_entities_is_dict(self):
        """entities debe ser un dict."""
        for s in SCENARIOS:
            self.assertIsInstance(s.entities, dict,
                                  f"entities de '{s.id}' debe ser dict")


class TestSimulatorVerbose(unittest.TestCase):
    """Pruebas informativas (no bloqueantes)."""

    def test_list_all_scenarios(self):
        """Lista todos los escenarios con sus metadatos."""
        print(f"\n  Total escenarios: {len(SCENARIOS)}")
        for s in SCENARIOS:
            print(f"    📋 {s.id}: {s.title[:50]}")
            print(f"       Canal: {s.channel} | Pasos: {len(s.steps)} | Telegram: {len(s.telegram)}")

    def test_scenario_diversity(self):
        """Verifica que hay variedad de canales."""
        channels = set(s.channel for s in SCENARIOS)
        print(f"\n  Canales disponibles: {', '.join(sorted(channels))}")
        self.assertGreaterEqual(len(channels), 3,
                                f"Debe haber al menos 3 canales distintos, hay {len(channels)}")


class TestDemoData(unittest.TestCase):
    """Pruebas del archivo client_demo.json."""

    def test_client_demo_json_exists(self):
        """Verifica que existe client_demo.json con datos."""
        demo_path = 'simulators/client_demo.json'
        if not os.path.exists(demo_path):
            self.skipTest("client_demo.json no encontrado")
        with open(demo_path) as f:
            data = json.load(f)
        self.assertIsInstance(data, (list, dict),
                              "client_demo.json debe ser un objeto JSON válido")
        items = data if isinstance(data, list) else [data]
        self.assertGreaterEqual(len(items), 1,
                                "client_demo.json debe tener datos")


if __name__ == '__main__':
    unittest.main()
