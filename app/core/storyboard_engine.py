"""
Live Pre-Sales Storyboard Engine ("Soutenance Live").

Orchestrates timed multi-phase demonstration scenarios across simulated devices
(Nominal -> Energy Drift / Sensor Fault -> Critical Alarm Spike -> Corrective Recovery),
injecting realistic anomalies into StorageRepository for live ThingsBoard demos.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.variable import AnomalyType, VariableType
from app.storage.repository import StorageRepository

logger = logging.getLogger("iot_sim.storyboard")


class StoryboardPhase(BaseModel):
    """Single timed step within a live demonstration storyboard."""
    phase_number: int
    title: str
    description: str
    duration_sec: int
    anomaly_mode: AnomalyType
    anomaly_magnitude: float = 35.0
    target_keywords: List[str] = []


class StoryboardDefinition(BaseModel):
    """Pre-configured timed demo scenario."""
    id: str
    name: str
    description: str
    total_duration_sec: int
    phases: List[StoryboardPhase]


def get_storyboards() -> List[StoryboardDefinition]:
    """Returns curated live presentation storyboards."""
    return [
        StoryboardDefinition(
            id="demo_bacs_derive",
            name="Soutenance Décret BACS — Dérive Énergétique & Optimisation",
            description="Scénario guidé (60s) : Régime nominal -> Dérive lente CVC -> Pic critique & Alarme -> Retour à l'économie.",
            total_duration_sec=60,
            phases=[
                StoryboardPhase(
                    phase_number=1,
                    title="Régime Nominal Optimisé",
                    description="Tous les équipements fonctionnent dans leurs bornes nominales (économie BACS active).",
                    duration_sec=15,
                    anomaly_mode=AnomalyType.NONE,
                    anomaly_magnitude=0.0,
                ),
                StoryboardPhase(
                    phase_number=2,
                    title="Dérive Énergétique CVC (Encrassement / Mauvais Réglage)",
                    description="Injection d'une dérive progressive (+25) sur les puissances et températures.",
                    duration_sec=15,
                    anomaly_mode=AnomalyType.DRIFT,
                    anomaly_magnitude=25.0,
                    target_keywords=["puissance", "temp", "debit", "conso"],
                ),
                StoryboardPhase(
                    phase_number=3,
                    title="Pic de Surconsommation & Alarme ThingsBoard",
                    description="Excursion critique (+60) déclenchant les seuils d'alarmes ThingsBoard.",
                    duration_sec=15,
                    anomaly_mode=AnomalyType.SPIKE,
                    anomaly_magnitude=60.0,
                    target_keywords=["puissance", "temp", "pression", "courant"],
                ),
                StoryboardPhase(
                    phase_number=4,
                    title="Action Corrective & Retour au Nominal",
                    description="Acquittement et rééquilibrage automatique : retour aux valeurs optimisées.",
                    duration_sec=15,
                    anomaly_mode=AnomalyType.NONE,
                    anomaly_magnitude=0.0,
                ),
            ],
        ),
        StoryboardDefinition(
            id="demo_maintenance_predictive",
            name="Maintenance Prédictive — Panne Capteur & Perte Liaison",
            description="Scénario guidé (60s) : Nominal -> Capteur figé (Freeze) -> Perte bus terrain (Timeout) -> Rétablissement.",
            total_duration_sec=60,
            phases=[
                StoryboardPhase(
                    phase_number=1,
                    title="Acquisition Nominale",
                    description="Télémétries et flux temps réel stables.",
                    duration_sec=15,
                    anomaly_mode=AnomalyType.NONE,
                    anomaly_magnitude=0.0,
                ),
                StoryboardPhase(
                    phase_number=2,
                    title="Blocage Capteur (Freeze)",
                    description="Valeur figée simulant un capteur bloqué mécaniquement.",
                    duration_sec=15,
                    anomaly_mode=AnomalyType.FREEZE,
                    anomaly_magnitude=0.0,
                    target_keywords=["temp", "pression", "niveau", "debit"],
                ),
                StoryboardPhase(
                    phase_number=3,
                    title="Perte Liaison Terrain (Timeout)",
                    description="Interruption d'émission simulant une coupure bus RS485/MQTT.",
                    duration_sec=15,
                    anomaly_mode=AnomalyType.TIMEOUT,
                    anomaly_magnitude=0.0,
                    target_keywords=["temp", "pression", "puissance"],
                ),
                StoryboardPhase(
                    phase_number=4,
                    title="Rétablissement & Résilience",
                    description="Reprise normale des publications temps réel.",
                    duration_sec=15,
                    anomaly_mode=AnomalyType.NONE,
                    anomaly_magnitude=0.0,
                ),
            ],
        ),
    ]


class StoryboardManager:
    """Singleton orchestrator running at most one live storyboard in background."""

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self.running: bool = False
        self.active_storyboard_id: Optional[str] = None
        self.active_storyboard_name: Optional[str] = None
        self.current_phase: int = 0
        self.total_phases: int = 0
        self.phase_title: str = ""
        self.phase_description: str = ""
        self.started_at: Optional[float] = None

    def _apply_phase_anomalies(self, phase: StoryboardPhase, repo: StorageRepository) -> int:
        """Applies or clears anomaly flags on matching telemetry variables."""
        variables = repo.get_variables()
        updated = 0
        for v in variables:
            if v.var_type != VariableType.TELEMETRY or not v.enabled:
                continue
            if phase.anomaly_mode == AnomalyType.NONE:
                if v.anomaly != AnomalyType.NONE:
                    v.anomaly = AnomalyType.NONE
                    repo.save_variable(v)
                    updated += 1
            else:
                matches = not phase.target_keywords or any(
                    kw in v.id.lower() or kw in v.name.lower() for kw in phase.target_keywords
                )
                if matches:
                    v.anomaly = phase.anomaly_mode
                    v.anomaly_magnitude = phase.anomaly_magnitude
                    repo.save_variable(v)
                    updated += 1
        return updated

    async def _run_storyboard(self, sb: StoryboardDefinition):
        repo = StorageRepository()
        try:
            logger.info(f"🎬 [STORYBOARD] Démarrage : '{sb.name}' ({len(sb.phases)} phases)")
            for phase in sb.phases:
                if not self.running:
                    break
                self.current_phase = phase.phase_number
                self.phase_title = phase.title
                self.phase_description = phase.description
                count = self._apply_phase_anomalies(phase, repo)
                logger.info(
                    f"🎬 [STORYBOARD Phase {phase.phase_number}/{len(sb.phases)}] "
                    f"{phase.title} ({phase.anomaly_mode.value}, {count} variables ciblées)"
                )
                await asyncio.sleep(phase.duration_sec)
        except asyncio.CancelledError:
            logger.info("⏹️ [STORYBOARD] Scénario interrompu par l'utilisateur.")
        finally:
            # Always restore clean nominal state on finish or stop
            clean_phase = StoryboardPhase(
                phase_number=0,
                title="Fin",
                description="",
                duration_sec=0,
                anomaly_mode=AnomalyType.NONE,
            )
            self._apply_phase_anomalies(clean_phase, repo)
            self.running = False
            self.current_phase = 0
            self.phase_title = "Terminé (État nominal restauré)"
            self.phase_description = ""
            logger.info("✅ [STORYBOARD] Scénario terminé, état nominal restauré.")

    async def start(self, storyboard_id: str) -> Dict[str, Any]:
        boards = {b.id: b for b in get_storyboards()}
        if storyboard_id not in boards:
            raise ValueError(f"Storyboard '{storyboard_id}' introuvable.")

        await self.stop()
        sb = boards[storyboard_id]
        self.running = True
        self.active_storyboard_id = sb.id
        self.active_storyboard_name = sb.name
        self.total_phases = len(sb.phases)
        self.started_at = time.time()
        self._task = asyncio.create_task(self._run_storyboard(sb))
        return self.status()

    async def stop(self) -> Dict[str, Any]:
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        return self.status()

    def status(self) -> Dict[str, Any]:
        elapsed = round(time.time() - self.started_at, 1) if (self.running and self.started_at) else 0.0
        return {
            "running": self.running,
            "storyboard_id": self.active_storyboard_id,
            "storyboard_name": self.active_storyboard_name,
            "current_phase": self.current_phase,
            "total_phases": self.total_phases,
            "phase_title": self.phase_title,
            "phase_description": self.phase_description,
            "elapsed_sec": elapsed,
        }


storyboard_manager = StoryboardManager()
