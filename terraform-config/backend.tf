terraform {
    backend "gcs" {
        bucket  = "second-brain-fw-terraform-config"
        prefix  = "terraform/state"
    }
}
