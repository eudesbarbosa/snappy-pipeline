# -*- coding: utf-8 -*-
"""Tests for the ngs_mapping workflow module code"""

import pytest
import ruamel.yaml as yaml
import textwrap

from snakemake.io import Wildcards

from snappy_pipeline.workflows.ngs_mapping import NgsMappingWorkflow

from .conftest import patch_module_fs

__author__ = "Manuel Holtgrewe <manuel.holtgrewe@bihealth.de>"


@pytest.fixture(scope="module")  # otherwise: performance issues
def minimal_config():
    """Return YAML parsing result for (germline) configuration"""
    return yaml.round_trip_load(
        textwrap.dedent(
            r"""
        static_data_config:
          reference:
            path: /path/to/ref.fa

        step_config:
          ngs_mapping:
            target_coverage_report:
              path_target_interval_list_mapping:
              - pattern: "Agilent SureSelect Human All Exon V6.*"
                name: Agilent_SureSelect_Human_All_Exon_V6
                path: path/to/SureSelect_Human_All_Exon_V6_r2.bed
            compute_coverage_bed: true
            bwa:
              path_index: /path/to/bwa/index.fasta
            star:
              path_index: /path/to/star/index

        data_sets:
          first_batch:
            file: sheet.tsv
            search_patterns:
            - {'left': '*/*/*_R1.fastq.gz', 'right': '*/*/*_R2.fastq.gz'}
            search_paths: ['/path']
            type: germline_variants
            naming_scheme: only_secondary_id
        """
        ).lstrip()
    )


@pytest.fixture
def ngs_mapping_workflow(
    dummy_workflow,
    minimal_config,
    dummy_cluster_config,
    config_lookup_paths,
    work_dir,
    config_paths,
    germline_sheet_fake_fs,
    aligner_indices_fake_fs,
    mocker,
):
    """Return NgsMappingWorkflow object pre-configured with germline sheet"""
    # Patch out file-system related things in abstract (the crawling link in step is defined there)
    patch_module_fs("snappy_pipeline.workflows.abstract", germline_sheet_fake_fs, mocker)
    # Patch out files for aligner indices
    patch_module_fs("snappy_pipeline.workflows.ngs_mapping", aligner_indices_fake_fs, mocker)
    # Construct the workflow object
    return NgsMappingWorkflow(
        dummy_workflow,
        minimal_config,
        dummy_cluster_config,
        config_lookup_paths,
        config_paths,
        work_dir,
    )


# Tests for BwaStepPart ---------------------------------------------------------------------------


def test_bwa_step_part_get_args(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"library_name": "P001-N1-DNA1-WGS1"})
    expected = {
        "input": {
            "reads_left": ["work/input_links/P001-N1-DNA1-WGS1/FCXXXXXX/L001/P001_R1.fastq.gz"],
            "reads_right": ["work/input_links/P001-N1-DNA1-WGS1/FCXXXXXX/L001/P001_R2.fastq.gz"],
        },
        "platform": "ILLUMINA",
        "sample_name": "P001-N1-DNA1-WGS1",
    }
    assert ngs_mapping_workflow.get_args("bwa", "run")(wildcards) == expected


def test_bwa_step_part_get_input_files(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"library_name": "P001-N1-DNA1-WGS1"})
    expected = "work/input_links/P001-N1-DNA1-WGS1/.done"
    assert ngs_mapping_workflow.get_input_files("bwa", "run")(wildcards) == expected


def test_bwa_step_part_get_output_files(ngs_mapping_workflow):
    expected = {
        "bam": "work/bwa.{library_name}/out/bwa.{library_name}.bam",
        "bam_bai": "work/bwa.{library_name}/out/bwa.{library_name}.bam.bai",
        "bam_bai_md5": "work/bwa.{library_name}/out/bwa.{library_name}.bam.bai.md5",
        "bam_md5": "work/bwa.{library_name}/out/bwa.{library_name}.bam.md5",
        "report_bamstats_html": "work/bwa.{library_name}/report/bam_qc/bwa.{library_name}.bam.bamstats.html",
        "report_bamstats_html_md5": "work/bwa.{library_name}/report/bam_qc/bwa.{library_name}.bam.bamstats.html.md5",
        "report_bamstats_txt": "work/bwa.{library_name}/report/bam_qc/bwa.{library_name}.bam.bamstats.txt",
        "report_bamstats_txt_md5": "work/bwa.{library_name}/report/bam_qc/bwa.{library_name}.bam.bamstats.txt.md5",
        "report_flagstats_txt": "work/bwa.{library_name}/report/bam_qc/bwa.{library_name}.bam.flagstats.txt",
        "report_flagstats_txt_md5": "work/bwa.{library_name}/report/bam_qc/bwa.{library_name}.bam.flagstats.txt.md5",
        "report_idxstats_txt": "work/bwa.{library_name}/report/bam_qc/bwa.{library_name}.bam.idxstats.txt",
        "report_idxstats_txt_md5": "work/bwa.{library_name}/report/bam_qc/bwa.{library_name}.bam.idxstats.txt.md5",
    }
    assert ngs_mapping_workflow.get_output_files("bwa", "run") == expected


def test_bwa_step_part_get_log_file(ngs_mapping_workflow):
    expected = {
        "log": "work/bwa.{library_name}/log/bwa.{library_name}.log",
        "log_md5": "work/bwa.{library_name}/log/bwa.{library_name}.log.md5",
        "conda_info": "work/bwa.{library_name}/log/bwa.{library_name}.conda_info.txt",
        "conda_info_md5": "work/bwa.{library_name}/log/bwa.{library_name}.conda_info.txt.md5",
        "conda_list": "work/bwa.{library_name}/log/bwa.{library_name}.conda_list.txt",
        "conda_list_md5": "work/bwa.{library_name}/log/bwa.{library_name}.conda_list.txt.md5",
    }
    assert ngs_mapping_workflow.get_log_file("bwa", "run") == expected


# Tests for StarStepPart --------------------------------------------------------------------------


def test_star_step_part_get_args(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"library_name": "P001-N1-DNA1-WGS1"})
    expected = {
        "input": {
            "reads_left": ["work/input_links/P001-N1-DNA1-WGS1/FCXXXXXX/L001/P001_R1.fastq.gz"],
            "reads_right": ["work/input_links/P001-N1-DNA1-WGS1/FCXXXXXX/L001/P001_R2.fastq.gz"],
        },
        "platform": "ILLUMINA",
        "sample_name": "P001-N1-DNA1-WGS1",
    }
    assert ngs_mapping_workflow.get_args("star", "run")(wildcards) == expected


def test_star_step_part_get_input_files(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"library_name": "P001-N1-DNA1-WGS1"})
    expected = "work/input_links/P001-N1-DNA1-WGS1/.done"
    assert ngs_mapping_workflow.get_input_files("star", "run")(wildcards) == expected


def test_star_step_part_get_output_files(ngs_mapping_workflow):
    expected = {
        "bam": "work/star.{library_name}/out/star.{library_name}.bam",
        "bam_bai": "work/star.{library_name}/out/star.{library_name}.bam.bai",
        "bam_bai_md5": "work/star.{library_name}/out/star.{library_name}.bam.bai.md5",
        "bam_md5": "work/star.{library_name}/out/star.{library_name}.bam.md5",
        "report_bamstats_html": "work/star.{library_name}/report/bam_qc/star.{library_name}.bam.bamstats.html",
        "report_bamstats_html_md5": "work/star.{library_name}/report/bam_qc/star.{library_name}.bam.bamstats.html.md5",
        "report_bamstats_txt": "work/star.{library_name}/report/bam_qc/star.{library_name}.bam.bamstats.txt",
        "report_bamstats_txt_md5": "work/star.{library_name}/report/bam_qc/star.{library_name}.bam.bamstats.txt.md5",
        "report_flagstats_txt": "work/star.{library_name}/report/bam_qc/star.{library_name}.bam.flagstats.txt",
        "report_flagstats_txt_md5": "work/star.{library_name}/report/bam_qc/star.{library_name}.bam.flagstats.txt.md5",
        "report_idxstats_txt": "work/star.{library_name}/report/bam_qc/star.{library_name}.bam.idxstats.txt",
        "report_idxstats_txt_md5": "work/star.{library_name}/report/bam_qc/star.{library_name}.bam.idxstats.txt.md5",
    }
    assert ngs_mapping_workflow.get_output_files("star", "run") == expected


def test_star_step_part_get_log_file(ngs_mapping_workflow):
    expected = {
        "log": "work/star.{library_name}/log/star.{library_name}.log",
        "log_md5": "work/star.{library_name}/log/star.{library_name}.log.md5",
        "conda_info": "work/star.{library_name}/log/star.{library_name}.conda_info.txt",
        "conda_info_md5": "work/star.{library_name}/log/star.{library_name}.conda_info.txt.md5",
        "conda_list": "work/star.{library_name}/log/star.{library_name}.conda_list.txt",
        "conda_list_md5": "work/star.{library_name}/log/star.{library_name}.conda_list.txt.md5",
    }
    assert ngs_mapping_workflow.get_log_file("star", "run") == expected


# Tests for ExternalStepPart ----------------------------------------------------------------------


# TODO(holtgrewe): the fake file system should be setup with fake BAM files.
def test_external_step_part_get_args(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"library_name": "P001-N1-DNA1-WGS1"})
    expected = {"input": [], "platform": "EXTERNAL", "sample_name": "P001-N1-DNA1-WGS1"}
    assert ngs_mapping_workflow.get_args("external", "run")(wildcards) == expected


def test_external_step_part_get_input_files(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"library_name": "P001-N1-DNA1-WGS1"})
    expected = "work/input_links/P001-N1-DNA1-WGS1/.done"
    assert ngs_mapping_workflow.get_input_files("external", "run")(wildcards) == expected


def test_external_step_part_get_output_files(ngs_mapping_workflow):
    expected = {
        "bam": "work/external.{library_name}/out/external.{library_name}.bam",
        "bam_bai": "work/external.{library_name}/out/external.{library_name}.bam.bai",
        "bam_bai_md5": "work/external.{library_name}/out/external.{library_name}.bam.bai.md5",
        "bam_md5": "work/external.{library_name}/out/external.{library_name}.bam.md5",
        "report_bamstats_txt": "work/external.{library_name}/report/bam_qc/external.{library_name}.bam.bamstats.txt",
        "report_bamstats_txt_md5": "work/external.{library_name}/report/bam_qc/external.{library_name}.bam.bamstats.txt.md5",
        "report_bamstats_html": "work/external.{library_name}/report/bam_qc/external.{library_name}.bam.bamstats.html",
        "report_bamstats_html_md5": "work/external.{library_name}/report/bam_qc/external.{library_name}.bam.bamstats.html.md5",
        "report_flagstats_txt": "work/external.{library_name}/report/bam_qc/external.{library_name}.bam.flagstats.txt",
        "report_flagstats_txt_md5": "work/external.{library_name}/report/bam_qc/external.{library_name}.bam.flagstats.txt.md5",
        "report_idxstats_txt": "work/external.{library_name}/report/bam_qc/external.{library_name}.bam.idxstats.txt",
        "report_idxstats_txt_md5": "work/external.{library_name}/report/bam_qc/external.{library_name}.bam.idxstats.txt.md5",
    }
    assert ngs_mapping_workflow.get_output_files("external", "run") == expected


# Tests for GatkPostBamStepPart -------------------------------------------------------------------


def test_gatk_post_bam_step_part_get_input_files(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"mapper": "bwa", "library_name": "library"})
    expected = "work/{mapper}.{library_name}/out/{mapper}.{library_name}.bam"
    assert ngs_mapping_workflow.get_input_files("gatk_post_bam", "run") == expected


def test_gatk_post_bam_step_part_get_output_files(ngs_mapping_workflow):
    expected = {
        "bai_md5_realigned": "work/{mapper}.{library_name}/out/{mapper}.{library_name}.realigned.bam.bai.md5",
        "bai_md5_recalibrated": "work/{mapper}.{library_name}/out/{mapper}.{library_name}.realigned.recalibrated.bam.bai.md5",
        "bai_realigned": "work/{mapper}.{library_name}/out/{mapper}.{library_name}.realigned.bam.bai",
        "bai_recalibrated": "work/{mapper}.{library_name}/out/{mapper}.{library_name}.realigned.recalibrated.bam.bai",
        "bam_md5_realigned": "work/{mapper}.{library_name}/out/{mapper}.{library_name}.realigned.bam.md5",
        "bam_md5_recalibrated": "work/{mapper}.{library_name}/out/{mapper}.{library_name}.realigned.recalibrated.bam.md5",
        "bam_realigned": "work/{mapper}.{library_name}/out/{mapper}.{library_name}.realigned.bam",
        "bam_recalibrated": "work/{mapper}.{library_name}/out/{mapper}.{library_name}.realigned.recalibrated.bam",
    }
    assert ngs_mapping_workflow.get_output_files("gatk_post_bam", "run") == expected


def test_gatk_post_bam_step_part_get_log_file(ngs_mapping_workflow):
    expected = "work/{mapper}.{library_name}/log/snakemake.gatk_post_bam.log"
    assert ngs_mapping_workflow.get_log_file("gatk_post_bam", "run") == expected


# Tests for LinkOutBamStepPart --------------------------------------------------------------------


def test_link_out_bam_step_part_get_input_files(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"mapper": "bwa", "library_name": "library"})
    expected = [
        "work/bwa.library/out/bwa.library.bam",
        "work/bwa.library/out/bwa.library.bam.bai",
        "work/bwa.library/out/bwa.library.bam.md5",
        "work/bwa.library/out/bwa.library.bam.bai.md5",
    ]
    assert ngs_mapping_workflow.get_input_files("link_out_bam", "run")(wildcards) == expected


def test_link_out_bam_step_part_get_output_files(ngs_mapping_workflow):
    expected = [
        "output/{mapper}.{library_name}/out/{mapper}.{library_name}.bam",
        "output/{mapper}.{library_name}/out/{mapper}.{library_name}.bam.bai",
        "output/{mapper}.{library_name}/out/{mapper}.{library_name}.bam.md5",
        "output/{mapper}.{library_name}/out/{mapper}.{library_name}.bam.bai.md5",
    ]
    assert ngs_mapping_workflow.get_output_files("link_out_bam", "run") == expected


def test_link_out_bam_step_part_get_shell_cmd(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"mapper": "bwa", "library_name": "library"})
    actual = ngs_mapping_workflow.get_shell_cmd("link_out_bam", "run", wildcards)
    expected = textwrap.dedent(
        r"""
        test -L output/bwa.library/out/bwa.library.bam || ln -sr work/bwa.library/out/bwa.library.bam output/bwa.library/out/bwa.library.bam
        test -L output/bwa.library/out/bwa.library.bam.bai || ln -sr work/bwa.library/out/bwa.library.bam.bai output/bwa.library/out/bwa.library.bam.bai
        test -L output/bwa.library/out/bwa.library.bam.md5 || ln -sr work/bwa.library/out/bwa.library.bam.md5 output/bwa.library/out/bwa.library.bam.md5
        test -L output/bwa.library/out/bwa.library.bam.bai.md5 || ln -sr work/bwa.library/out/bwa.library.bam.bai.md5 output/bwa.library/out/bwa.library.bam.bai.md5
        """
    ).strip()
    assert actual == expected


# Tests for TargetCoverageReportStepPart ----------------------------------------------------------


def test_target_coverage_report_step_part_run_get_input_files(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"mapper_lib": "bwa.library"})
    expected = {
        "bam": "work/bwa.library/out/bwa.library.bam",
        "bai": "work/bwa.library/out/bwa.library.bam.bai",
    }
    assert (
        ngs_mapping_workflow.get_input_files("target_coverage_report", "run")(wildcards) == expected
    )


def test_target_coverage_report_step_part_collect_get_input_files(ngs_mapping_workflow):
    wildcards = Wildcards(fromdict={"mapper_lib": "bwa"})
    expected = [
        "work/bwa.P001-N1-DNA1-WGS1/report/cov_qc/bwa.P001-N1-DNA1-WGS1.txt",
        "work/bwa.P002-N1-DNA1-WGS1/report/cov_qc/bwa.P002-N1-DNA1-WGS1.txt",
        "work/bwa.P003-N1-DNA1-WGS1/report/cov_qc/bwa.P003-N1-DNA1-WGS1.txt",
        "work/bwa.P004-N1-DNA1-WGS1/report/cov_qc/bwa.P004-N1-DNA1-WGS1.txt",
        "work/bwa.P005-N1-DNA1-WGS1/report/cov_qc/bwa.P005-N1-DNA1-WGS1.txt",
        "work/bwa.P006-N1-DNA1-WGS1/report/cov_qc/bwa.P006-N1-DNA1-WGS1.txt",
    ]
    print(ngs_mapping_workflow.get_input_files("target_coverage_report", "collect")(wildcards))
    actual = ngs_mapping_workflow.get_input_files("target_coverage_report", "collect")(wildcards)
    assert actual == expected


def test_target_coverage_report_step_part_get_output_files(ngs_mapping_workflow):
    expected = {
        "txt": "work/{mapper_lib}/report/cov_qc/{mapper_lib}.txt",
        "txt_md5": "work/{mapper_lib}/report/cov_qc/{mapper_lib}.txt.md5",
    }
    assert ngs_mapping_workflow.get_output_files("target_coverage_report", "run") == expected


def test_target_coverage_report_step_part_run_get_log_file(ngs_mapping_workflow):
    expected = "work/{mapper_lib}/log/snakemake.target_coverage.log"
    assert ngs_mapping_workflow.get_log_file("target_coverage_report", "run") == expected


def test_target_coverage_report_step_part_collect_get_log_file(ngs_mapping_workflow):
    expected = "work/target_cov_report/log/snakemake.target_coverage.log"
    assert ngs_mapping_workflow.get_log_file("target_coverage_report", "colllect") == expected


def test_target_coverage_report_step_part_update_cluster_config(
    ngs_mapping_workflow, dummy_cluster_config
):
    """Test that the update_cluster_config has been called for the genome coverage report step
    part and the necessary steps are present
    """
    actual = set(dummy_cluster_config["ngs_mapping_target_coverage_report_run"].keys())
    expected = {"mem", "time", "ntasks"}
    assert actual == expected


# Tests for GenomeCoverageReportStepPart ----------------------------------------------------------


def test_genome_coverage_report_step_part_get_input_files(ngs_mapping_workflow):
    expected = {
        "bam": "work/{mapper_lib}/out/{mapper_lib}.bam",
        "bai": "work/{mapper_lib}/out/{mapper_lib}.bam.bai",
    }
    assert ngs_mapping_workflow.get_input_files("genome_coverage_report", "run") == expected


def test_genome_coverage_report_step_part_get_output_files(ngs_mapping_workflow):
    expected = {
        "bed": "work/{mapper_lib}/report/coverage/{mapper_lib}.bed.gz",
        "tbi": "work/{mapper_lib}/report/coverage/{mapper_lib}.bed.gz.tbi",
    }
    assert ngs_mapping_workflow.get_output_files("genome_coverage_report", "run") == expected


def test_genome_coverage_report_step_part_get_log_file(ngs_mapping_workflow):
    expected = "work/{mapper_lib}/log/snakemake.genome_coverage.log"
    assert ngs_mapping_workflow.get_log_file("genome_coverage_report", "run") == expected


def test_genome_coverage_report_step_part_get_shell_cmd(ngs_mapping_workflow):
    cmd = ngs_mapping_workflow.get_shell_cmd("genome_coverage_report", "run", None)
    # The shell command returns a static blob and thus we only check for some important keywords.
    # The actual functionality has to be tested in an integration/system test.
    assert "samtools depth" in cmd
    assert "bgzip -c" in cmd
    assert "tabix {output.bed}" in cmd


def test_genome_coverage_report_step_part_update_cluster_config(
    ngs_mapping_workflow, dummy_cluster_config
):
    """Test that the update_cluster_config has been called for the genome coverage report step
    part and the necessary steps are present
    """
    actual = set(dummy_cluster_config["ngs_mapping_genome_coverage_report_run"].keys())
    expected = {"mem", "time", "ntasks"}
    assert actual == expected


# Tests for NgsMappingWorkflow --------------------------------------------------------------------


def test_ngs_mapping_workflow_steps(ngs_mapping_workflow):
    """Tests simple functionality of the workflow: checks if sub steps are created,
    i.e., the tools associated with gene expression quantification."""
    # Check created sub steps
    expected = [
        "bwa",
        "external",
        "gatk_post_bam",
        "genome_coverage_report",
        "link_in",
        "link_out",
        "link_out_bam",
        "minimap2",
        "ngmlr",
        "picard_hs_metrics",
        "star",
        "target_coverage_report",
    ]
    actual = list(sorted(ngs_mapping_workflow.sub_steps.keys()))
    assert actual == expected


def test_ngs_mapping_workflow_files(ngs_mapping_workflow):
    """Tests simple functionality of the workflow: checks if file structure is created according
    to the expected results from the tools, namely: bwa, external, gatk_post_bam,
    genome_coverage_report, link_in, link_out, link_out_bam, minimap2, ngmlr, picard_hs_metrics,
    star, target_coverage_report."""
    # Check result file construction
    expected = [
        "output/bwa.P00{i}-N1-DNA1-WGS1/out/bwa.P00{i}-N1-DNA1-WGS1.{ext}".format(i=i, ext=ext)
        for i in range(1, 7)
        for ext in ("bam", "bam.bai", "bam.md5", "bam.bai.md5")
    ]
    expected += [
        "output/bwa.P00{i}-N1-DNA1-WGS1/log/bwa.P00{i}-N1-DNA1-WGS1.{ext}".format(i=i, ext=ext)
        for i in range(1, 7)
        for ext in (
            "log",
            "conda_info.txt",
            "conda_list.txt",
            "log.md5",
            "conda_info.txt.md5",
            "conda_list.txt.md5",
        )
    ]
    expected += [
        "output/bwa.P00{i}-N1-DNA1-WGS1/report/bam_qc/bwa.P00{i}-N1-DNA1-WGS1.bam.{stats}.{ext}".format(
            i=i, stats=stats, ext=ext
        )
        for ext in ("txt", "txt.md5")
        for i in range(1, 7)
        for stats in ("bamstats", "flagstats", "idxstats")
    ]
    expected += [
        "output/bwa.P00{i}-N1-DNA1-WGS1/report/bam_qc/bwa.P00{i}-N1-DNA1-WGS1.bam.bamstats.{ext}".format(
            i=i, ext=ext
        )
        for ext in ("html", "html.md5")
        for i in range(1, 7)
    ]
    expected += [
        "output/bwa.P00{i}-N1-DNA1-WGS1/report/cov_qc/bwa.P00{i}-N1-DNA1-WGS1.{ext}".format(
            i=i, ext=ext
        )
        for ext in ("txt", "txt.md5")
        for i in range(1, 7)
    ]
    expected += [
        "output/target_cov_report/out/target_cov_report.txt",
        "output/target_cov_report/out/target_cov_report.txt.md5",
    ]
    expected += [
        "output/bwa.P00{i}-N1-DNA1-WGS1/report/coverage/bwa.P00{i}-N1-DNA1-WGS1.{ext}".format(
            i=i, ext=ext
        )
        for i in range(1, 7)
        for ext in ("bed.gz", "bed.gz.tbi")
    ]
    assert sorted(ngs_mapping_workflow.get_result_files()) == sorted(expected)