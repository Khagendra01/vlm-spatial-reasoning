import json

d = json.load(open('results/equiorient/pilot_run_v2_corrected_matrix.json',
                   encoding='utf-8'))
print('lambda_selected:', d['lambda_selected'])
print('repo_commit:', d.get('repo_commit', 'n/a'))
for arm in ['augmentation_only', 'output_consistency', 'latent_invariance',
            'equiorient', 'wrong_geometry_equiorient']:
    a = d['per_arm_val'][arm]
    print(f"{arm:26s} val {a['val_acc']:.4f} | holdout {a['holdout_VoH_accuracy']:.4f} "
          f"| zcorr {a['holdout_VoH_accuracy_z_corrupted']:.4f} "
          f"| both {a['paired_both_correct_VoH']:.4f} "
          f"| latent {a['latent_equivariance_error_VoH']:.4f} "
          f"| probe {a['depth_probe_holdout_acc']:.4f} "
          f"| probe_zd {a['depth_probe_z_d_holdout_acc']:.4f} "
          f"| ans {a['train_loss']['answer']} "
          f"| struct {a['train_loss']['structural']}")
