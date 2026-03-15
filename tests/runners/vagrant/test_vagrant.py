# Copyright (c) 2026 Mathias Ertl
# Licensed under the MIT License. See LICENSE file for details.

"""Test vagrant tutorials."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_subprocess import FakeProcess

from structured_tutorials.errors import (
    ConfigurationException,
    RequiredExecutableNotFoundError,
    RunTutorialException,
)
from structured_tutorials.models import TutorialModel
from structured_tutorials.runners.vagrant import VagrantRunner


@pytest.mark.tutorial("vagrant")
def test_vagrant(fp: FakeProcess, runner: VagrantRunner) -> None:
    """Test running a vagrant tutorial."""
    path = runner.tutorial.configuration.run.context["tutorial_path"]
    tmp_path = "/tmp/mocked.txt"

    # Setup of the tutorial
    fp.register(["vagrant", "up"])

    # Actual tutorial
    fp.register(["vagrant", "ssh", "default", "-c", "ls"])
    fp.register(["vagrant", "upload", path, "/tmp/does/not/exist/vagrant.yaml", "default"])
    fp.register(["vagrant", "upload", tmp_path, "/tmp/rendered-template.yaml", "default"])
    fp.register(["vagrant", "ssh", "machine_a", "-c", "ls /"])  # first ls on two VMs
    fp.register(["vagrant", "ssh", "machine_b", "-c", "ls /"])
    fp.register(["vagrant", "ssh", "default", "-c", "ls /"])
    fp.register(["vagrant", "ssh", "default", "-c", "tee /tmp/stdin.test"])
    fp.register(["vagrant", "ssh", "default", "-c", "cat /tmp/stdin.test"])

    # Cleanup of tutorial
    fp.register(["vagrant", "destroy", "-f"])

    with patch("structured_tutorials.runners.vagrant.tempfile.NamedTemporaryFile") as mock_ntf:
        mock_file = MagicMock()
        mock_file.name = tmp_path
        mock_ntf.return_value.__enter__.return_value = mock_file

        runner.prepare_tutorial()
        runner.run()
        runner.cleanup_tutorial()


@pytest.mark.tutorial("vagrant-prepare-box")
def test_vagrant_prepare_box(fp: FakeProcess, runner: VagrantRunner) -> None:
    """Test running a vagrant tutorial where a box is prepared."""
    # preparation of box
    fp.register(["vagrant", "box", "list", "--machine-readable"])
    fp.register(["vagrant", "up"])
    fp.register(["vagrant", "package", "--output", "prepared-box.box"])
    fp.register(["vagrant", "destroy", "-f"])
    fp.register(["vagrant", "box", "add", "prepared-box", "prepared-box.box"])

    # Actually run the tutorial
    fp.register(["vagrant", "up"])
    fp.register(["vagrant", "ssh", "default", "-c", "ls"])
    fp.register(["vagrant", "destroy", "-f"])

    runner.prepare_tutorial()
    runner.run()
    runner.cleanup_tutorial()


@pytest.mark.tutorial("vagrant-prepare-box")
def test_vagrant_prepare_box_exists(fp: FakeProcess, runner: VagrantRunner) -> None:
    """Test running a vagrant tutorial where a box is prepared, but already exists."""
    # preparation of box
    fp.register(["vagrant", "box", "list", "--machine-readable"], stdout="a,b,box-name,prepared-box")

    # Actually run the tutorial
    fp.register(["vagrant", "up"])
    fp.register(["vagrant", "ssh", "default", "-c", "ls"])
    fp.register(["vagrant", "destroy", "-f"])

    runner.prepare_tutorial()
    runner.run()
    runner.cleanup_tutorial()


@pytest.mark.tutorial("vagrant-prepare-box")
def test_vagrant_prepare_box_vagrantfile_exists(
    tmp_path: Path, fp: FakeProcess, runner: VagrantRunner
) -> None:
    """Test running a vagrant tutorial where a box is prepared, but already exists."""
    runner.config.prepare_box.cwd = tmp_path  # type: ignore[union-attr]
    (tmp_path / "Vagrantfile").touch()

    # preparation of box
    fp.register(["vagrant", "box", "list", "--machine-readable"], stdout="a,b,box-name,prepared-box")

    # Actually run the tutorial
    fp.register(["vagrant", "up"])
    fp.register(["vagrant", "ssh", "default", "-c", "ls"])
    fp.register(["vagrant", "destroy", "-f"])

    runner.prepare_tutorial()
    runner.run()
    runner.cleanup_tutorial()


@pytest.mark.tutorial("vagrant-prepare-box")
def test_vagrant_prepare_vagrantfile_not_found(
    tmp_path: Path, fp: FakeProcess, runner: VagrantRunner
) -> None:
    """Test running a vagrant tutorial where the Vagrantfile is not found."""
    runner.config.prepare_box.cwd = tmp_path  # type: ignore[union-attr]

    with pytest.raises(ConfigurationException, match="Vagrantfile not found:"):
        runner.prepare_tutorial()


@pytest.mark.tutorial("vagrant-prepare-box")
def test_vagrant_prepare_vagrantfile_directory_not_found(
    tmp_path: Path, fp: FakeProcess, runner: VagrantRunner
) -> None:
    """Test running a vagrant tutorial where the folder where the Vagrantfile should be is not found."""
    runner.config.prepare_box.cwd = tmp_path / "foo"  # type: ignore[union-attr]

    with pytest.raises(ConfigurationException, match=r"Directory not found\."):
        runner.prepare_tutorial()


@pytest.mark.tutorial("vagrant-multi-machine")
def test_vagrant_with_multi_machine(fp: FakeProcess, runner: VagrantRunner) -> None:
    """Test running a vagrant tutorial for multiple machines."""
    tmp_path = "/tmp/mocked.txt"
    fp.register(["vagrant", "up"])
    fp.register(["vagrant", "ssh", "foo", "-c", "ls multi"])
    fp.register(["vagrant", "ssh", "bar", "-c", "ls multi"])
    fp.register(["vagrant", "ssh", "foo", "-c", "ls single"])
    fp.register(["vagrant", "ssh", "default", "-c", "ls no machines"])
    fp.register(["vagrant", "upload", "/tmp/mocked.txt", "/tmp/rendered-template.yaml", "foo"])
    fp.register(["vagrant", "upload", "/tmp/mocked.txt", "/tmp/rendered-template.yaml", "bar"])
    fp.register(["vagrant", "destroy", "-f"])

    with patch("structured_tutorials.runners.vagrant.tempfile.NamedTemporaryFile") as mock_ntf:
        mock_file = MagicMock()
        mock_file.name = tmp_path
        mock_ntf.return_value.__enter__.return_value = mock_file

        runner.prepare_tutorial()
        runner.run()
        runner.cleanup_tutorial()


@pytest.mark.tutorial("vagrant-multi-machine")
def test_vagrant_with_multi_machine_with_empty_machines(fp: FakeProcess, runner: VagrantRunner) -> None:
    """Test running a vagrant tutorial for multiple machines."""
    runner.tutorial.parts[0].commands[0].run.runner["machines"] = []  # type: ignore[union-attr]
    fp.register(["vagrant", "up"])
    fp.register(["vagrant", "ssh", "foo", "-c", "ls multi"])

    runner.prepare_tutorial()
    with pytest.raises(RunTutorialException, match=r"empty list of machines passed\."):
        runner.run()


@pytest.mark.tutorial("vagrant-cwd")
def test_vagrant_with_chdir(fp: FakeProcess, runner: VagrantRunner) -> None:
    """Test running a vagrant tutorial for multiple machines, and changing dirs."""
    tmp_path = "/tmp/mocked.txt"
    fp.register(["vagrant", "up"])
    fp.register(["vagrant", "ssh", "foo", "-c", "cd /tmp/ && ls multi"])
    fp.register(["vagrant", "ssh", "bar", "-c", "cd /tmp/ && ls multi"])
    fp.register(["vagrant", "ssh", "foo", "-c", "cd /tmp/ && ls overlap"])
    fp.register(["vagrant", "ssh", "bla", "-c", "ls overlap"])
    fp.register(["vagrant", "ssh", "foo", "-c", "cd /tmp/ && ls multi2"])
    fp.register(["vagrant", "ssh", "default", "-c", "ls multi2"])
    fp.register(["vagrant", "ssh", "default", "-c", "cd /new && ls 3"])
    fp.register(["vagrant", "ssh", "default", "-c", "cd /new && ls 4"])
    fp.register(["vagrant", "destroy", "-f"])

    with patch("structured_tutorials.runners.vagrant.tempfile.NamedTemporaryFile") as mock_ntf:
        mock_file = MagicMock()
        mock_file.name = tmp_path
        mock_ntf.return_value.__enter__.return_value = mock_file

        runner.prepare_tutorial()
        runner.run()
        runner.cleanup_tutorial()


@pytest.mark.tutorial("vagrant-update-env")
def test_update_environment(fp: FakeProcess, runner: VagrantRunner) -> None:
    """Test updating the environment."""
    # Actually run the tutorial
    fp.register(["vagrant", "up"])
    fp.register(["vagrant", "ssh", "default", "-c", "ls"])
    fp.register(["vagrant", "ssh", "default", "-c", 'echo export foo="bar" >> ~/.profile'])
    fp.register(["vagrant", "destroy", "-f"])

    runner.prepare_tutorial()
    runner.run()
    runner.cleanup_tutorial()


@pytest.mark.tutorial("vagrant")
def test_vagrant_raises_error(fp: FakeProcess, runner: VagrantRunner, simple_tutorial: TutorialModel) -> None:
    """Test case where vagrant raises an error."""
    fp.register(["vagrant", "up"], returncode=1)
    with pytest.raises(RunTutorialException, match=r"^vagrant up exited with status code 1\.$"):
        runner.prepare_tutorial()


@pytest.mark.tutorial("vagrant")
def test_vagrant_not_found(fp: FakeProcess, runner: VagrantRunner, simple_tutorial: TutorialModel) -> None:
    """Test case where vagrant is not found."""
    with patch("structured_tutorials.runners.vagrant.shutil.which", return_value=False):
        with pytest.raises(RequiredExecutableNotFoundError, match=r"^vagrant: Executable not found\.$"):
            VagrantRunner(tutorial=simple_tutorial)
